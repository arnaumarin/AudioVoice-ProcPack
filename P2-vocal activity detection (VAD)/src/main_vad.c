#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <sndfile.h>

#include "vad.h"
#include "vad_docopt.h"

#define DEBUG_VAD 0x1

int main(int argc, char *argv[])
{
  int verbose = 0; /* To show internal state of vad: verbose = DEBUG_VAD; */

  SNDFILE *sndfile_in, *sndfile_out = 0;
  SF_INFO sf_info;
  FILE *vadfile;
  int n_read = 0, i, j, initframes = 5;

  VAD_DATA *vad_data;
  VAD_STATE state, last_state;
  float *buffer, *buffer_zeros;
  int frame_size;                         /* in samples */
  float frame_duration, time_elapsed = 0; /* in seconds */

  /*last_undef_t1 & t2 are the bounds of every "MAYBE..." state in frames */
  unsigned int t, last_t, last_undef_t1 = 0, last_undef_t2 = 0; /* in frames */
  unsigned found_first_undef = 1;                               /* flag to check if the first frame of an undefined state has been found */
  char *input_wav, *output_vad, *output_wav;

  DocoptArgs args = docopt(argc, argv, /* help */ 1, /* version */ "2.0");
  float alpha0 = atof(args.alpha0);
  float alpha1 = atof(args.alpha1);
  float alpha2 = atof(args.alpha2);
  float time = atof(args.time);
  verbose = args.verbose ? DEBUG_VAD : 0;
  input_wav = args.input_wav;
  output_vad = args.output_vad;
  output_wav = args.output_wav;

  if (input_wav == 0 || output_vad == 0)
  {
    fprintf(stderr, "%s\n", args.usage_pattern);
    return -1;
  }

  /* Open input sound file */
  if ((sndfile_in = sf_open(input_wav, SFM_READ, &sf_info)) == 0)
  {
    fprintf(stderr, "Error opening input file %s (%s) %s\n", input_wav, strerror(errno), sf_strerror(NULL));
    return -1;
  }

  if (sf_info.channels != 1)
  {
    fprintf(stderr, "Error: the input file has to be mono: %s\n", input_wav);
    return -2;
  }

  /* Open vad file */
  if ((vadfile = fopen(output_vad, "wt")) == 0)
  {
    fprintf(stderr, "Error opening output vad file %s (%s)\n", output_vad, strerror(errno));
    return -1;
  }

  /* Open output sound file, with same format, channels, etc. than input */
  if (output_wav)
  {
    if ((sndfile_out = sf_open(output_wav, SFM_WRITE, &sf_info)) == 0)
    {
      fprintf(stderr, "Error opening output wav file %s (%s)\n", output_wav, strerror(errno));
      return -1;
    }
  }

  vad_data = vad_open(sf_info.samplerate, alpha0, alpha1, alpha2, time);
  /* Allocate memory for buffers */
  frame_size = vad_frame_size(vad_data);
  buffer = (float *)malloc(frame_size * sizeof(float));
  buffer_zeros = (float *)malloc(frame_size * sizeof(float));
  for (i = 0; i < frame_size; ++i)
    buffer_zeros[i] = 0.0F;

  frame_duration = (float)frame_size / (float)sf_info.samplerate;
  last_state = ST_UNDEF;

  for (t = last_t = 0;; t++)
  { /* For each frame ... */
    /* End loop when file has finished (or there is an error) */
    if ((n_read = sf_read_float(sndfile_in, buffer, frame_size)) != frame_size)
      break;

    if (sndfile_out != 0)
    {
      /* TODO: copy all the samples into sndfile_out */
      sf_write_float(sndfile_out, buffer, frame_size);
    }

    /*Update frame count */
    time_elapsed = (t - last_t) * frame_duration;
    state = vad(vad_data, buffer, &time_elapsed);

    //if the state has changed and its an "UNDEF" state (MAYBE SILENCE/VOICE), it sets the upper frame bound last_undef_t2
    if (state != last_state && (state == ST_MAYBE_SILENCE || state == ST_MAYBE_VOICE))
    {
      if (found_first_undef == 0) //check if its the first "U" in a chain of "U" states (keep the first one)
      {
        found_first_undef = 1;
        last_undef_t2 = t;
      }
    }
    else //reset flag
      found_first_undef = 0;

    if (verbose & DEBUG_VAD)
    {
      printf("time elapsed = %f t = %d last_t = %d last_undef_t2 = %d last_undef_t1 = %d\t", time_elapsed, t, last_t, last_undef_t2, last_undef_t1);
      vad_show_state(vad_data, stdout);
    }

    /* TODO: print only SILENCE and VOICE labels */
    /* As it is, it prints UNDEF segments but is should be merge to the proper value */
    if ((state != last_state && time_elapsed == 0))
    {
      //printf("entra if\n last undef t %d\n", last_undef_t2);
      if (t != last_t)
      {
        if (state != ST_INIT)
        {
          fprintf(vadfile, "%.5f\t%.5f\t%s\n", last_undef_t1 * frame_duration, last_undef_t2 * frame_duration, state2str(last_state));

          if (found_first_undef == -1)
            found_first_undef = 0;
          if (sndfile_out != 0 && state == ST_VOICE)
          {
            //set out file pointer (last_undef_t2 - last_undef_t1)*frame_size times back
            for (j = 0; j < (last_undef_t2 - last_undef_t1); j++)
              sf_seek(sndfile_out, -frame_size, SEEK_CUR);
            //print silences
            for (j = 0; j < (last_undef_t2 - last_undef_t1); j++)
              sf_write_float(sndfile_out, buffer_zeros, frame_size);
          }
          last_undef_t1 = last_undef_t2;
        }
      }
      last_state = state;
      last_t = t;
    }
  }

  state = vad_close(vad_data);

  /* TODO: what do you want to print, for last frames? */
  if (state == ST_MAYBE_VOICE || state == ST_MAYBE_SILENCE)
    state = last_state;
  if (sndfile_out != 0 && state == ST_SILENCE)  //print silences
  {
    for (j = 0; j < (t - last_undef_t1); j++)
      sf_seek(sndfile_out, -frame_size, SEEK_CUR);
    for (j = 0; j < (t - last_undef_t1); j++)
      sf_write_float(sndfile_out, buffer_zeros, frame_size);
  }
  fprintf(vadfile, "%.5f\t%.5f\t%s\n", (last_undef_t1)*frame_duration, t * frame_duration + n_read / (float)sf_info.samplerate, state2str(state));

  /* clean up: free memory, close open files */
  free(buffer);
  free(buffer_zeros);
  sf_close(sndfile_in);
  fclose(vadfile);
  if (sndfile_out)
    sf_close(sndfile_out);
  return 0;
}
