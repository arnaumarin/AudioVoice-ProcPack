#! /usr/bin/python3 -u

import struct

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from docopt import docopt
import numpy as np
from scipy.stats import multivariate_normal as gauss
import copy
def read_gmm(fileGMM):
    '''
       Reads the weights, means and convariances from a GMM
       stored using format "UPC: GMM V 2.0"
    '''

    header = b'UPC: GMM V 2.0\x00'

    try:
        with open(fileGMM, 'rb') as fpGmm:
            headIn = fpGmm.read(15)
    
            if headIn != header:
                print(f'ERROR: {fileGMM} is not a valid GMM file')
                exit(-1)

            numMix = struct.unpack('@I', fpGmm.read(4))[0]
            weights = np.array(struct.unpack(f'@{numMix}f', fpGmm.read(numMix * 4)))

            (numMix, numCof) = struct.unpack('@II', fpGmm.read(2 * 4))
            means = struct.unpack(f'@{numMix * numCof}f', fpGmm.read(numMix * numCof * 4))
            means = np.array(means).reshape(numMix, numCof)

            (numMix, numCof) = struct.unpack('@II', fpGmm.read(2 * 4))
            invStd = struct.unpack(f'@{numMix * numCof}f', fpGmm.read(numMix * numCof * 4))
            covs = np.array(invStd).reshape(numMix, numCof) ** -2

            return weights, means, covs
    except:
        raise Exception(f'Error al leer el fichero {fileGMM}')


def read_fmatrix(fileFM):
    '''
       Reads an fmatrix from a file
    '''
    try:
        with open(fileFM, 'rb') as fpFM:
            (numFrm, numCof) = struct.unpack('@II', fpFM.read(2 * 4))
            data = struct.unpack(f'@{numFrm * numCof}f', fpFM.read(numFrm * numCof * 4))
            data = np.array(data).reshape(numFrm, numCof)

            return data
    except:
        raise Exception(f'Error al leer el fichero {fileFM}')


def pdfGMM(X, weights, means, covs):
    '''
       Returns the probability density function (PDF) of a population X
       given a Gaussian Mixture Model (GMM) defined by its weights,
       means and covariances.
    '''

    pdf = np.zeros(len(X))
    for mix, weight in enumerate(weights):
        try:
            pdf += weight * gauss.pdf(X, mean=means[mix], cov=covs[mix])
        except:
            raise Exception(f'Error al calcular la mezcla {mix} del GMM')

    return pdf

def limsGMM(means, covs, fStd=3):
    '''
       Returns the maximum and minimum values of the mean plus/minus fStd
       times the standard deviation for a set of Gaussians defined by their
       means and convariances.
    '''

    numMix = len(means)

    min_ = means[0][:]
    max_ = means[0][:]

    for mix in range(numMix):
        min_ = np.min((min_, means[mix] - fStd * covs[mix] ** 0.5), axis=0)
        max_ = np.max((max_, means[mix] + fStd * covs[mix] ** 0.5), axis=0)

    margin = max(max_ - min_)

    return min_, max_

def plotGMM(fileGMM, xDim, yDim, percents, colorGmm, colorGmm2,filesFeat=None, fileGMM2=None, filesFeat2=None, colorFeat=None, colorFeat2=None, limits=None):
    weights, means, covs = read_gmm(fileGMM)
    if filesFeat:
        feats = np.ndarray((0, 2))
        for fileFeat in filesFeat:
            feat = read_fmatrix(fileFeat)
            feat = np.stack((feat[..., xDim], feat[..., yDim]), axis=-1)
            feats = np.concatenate((feats, feat))

    means = np.stack((means[..., xDim], means[..., yDim]), axis=-1)
    covs = np.stack((covs[..., xDim], covs[..., yDim]), axis=-1)

    if not limits:
        min_, max_ = limsGMM(means, covs)
        limits = (min_[0], max_[0], min_[1], max_[1])
    else:
        min_, max_ = (limits[0], limits[2]), (limits[1], limits[3])

    # Fijamos el número de muestras de manera que el valor esperado de muestras
    # en el percentil más estrecho sea 1000. Calculamos el más estrecho como el
    # valor mínimo de p*(1-p)

    numSmp = int(np.ceil(np.max(1000 / (percents * (1 - percents))) ** 0.5))

    if fileGMM2:
        weights2, means2, covs2 = read_gmm(fileGMM2)
        fig, axs = plt.subplots(2, ncols=2)
        ax1=axs[0,0]
        ax2=axs[0,1]
        ax3=axs[1,0]
        ax4=axs[1,1]
  
        feats2 = np.ndarray((0, 2))
        for fileFeat2 in filesFeat2:
            feat2 = read_fmatrix(fileFeat2)
            feat2 = np.stack((feat2[..., xDim], feat2[..., yDim]), axis=-1)
            feats2 = np.concatenate((feats2, feat2))
        ax1.scatter(feats[:, 0], feats[:, 1], 1, color=colorFeat,alpha=0.2)
        ax2.scatter(feats2[:, 0], feats2[:, 1], 1, color=colorFeat2,alpha=0.2)
        ax3.scatter(feats[:, 0], feats[:, 1], 1, color=colorFeat,alpha=0.2)
        ax4.scatter(feats2[:, 0], feats2[:, 1], 1, color=colorFeat2,alpha=0.2)

        means2 = np.stack((means2[..., xDim], means2[..., yDim]), axis=-1)
        covs2 = np.stack((covs2[..., xDim], covs2[..., yDim]), axis=-1)

        if not limits:
            min_2, max_2 = limsGMM(means2, covs2)
        else:
            min_2, max_2 = (limits[0], limits[2]), (limits[1], limits[3])
        
        x2 = np.linspace(min_2[0], max_2[0], numSmp)
        y2 = np.linspace(min_2[1], max_2[1], numSmp)
        X2, Y2 = np.meshgrid(x2, y2)
        XX2 = np.array([X2.ravel(), Y2.ravel()]).T
        Z2 = pdfGMM(XX2, weights2, means2, covs2)
        Z2 /= sum(Z2)
        Zsort2 = np.sort(Z2)
        Zacum2 = Zsort2.cumsum()

        Z2 = Z2.reshape(X2.shape)
        
        style2 = {'colors': [colorGmm2] * len(percents), 'linestyles': ['dotted', 'dashed', 'solid']}

        #parse directories into names
        ses1=filesFeat[0].split('/')
        ses2=filesFeat2[0].split('/')
        gmm1=fileGMM.split('/')
        gmm2=fileGMM2.split('/')

        ses1 = ses1[3]
        ses2 = ses2[3]
        gmm1=gmm1[3]
        gmm2=gmm2[3]

        gmm1=gmm1.split('.')
        gmm1=gmm1[0]
        gmm2=gmm2.split('.')
        gmm2=gmm2[0]

        ax1.title.set_text('GMM: '+gmm1+ ' LOC: '+ses1)
        ax2.title.set_text('GMM: '+gmm1+ ' LOC: '+ses2)
        ax3.title.set_text('GMM: '+gmm2+ ' LOC: '+ses1)
        ax4.title.set_text('GMM: '+gmm2+ ' LOC: '+ses2)
    else:
        ax1 = plt.subplot(111)
        ax1.scatter(feats[:, 0], feats[:, 1], .05, color=colorFeat)

    x = np.linspace(min_[0], max_[0], numSmp)
    y = np.linspace(min_[1], max_[1], numSmp)
    X, Y = np.meshgrid(x, y)

    XX = np.array([X.ravel(), Y.ravel()]).T

    Z = pdfGMM(XX, weights, means, covs)
    Z /= sum(Z)
    Zsort = np.sort(Z)
    Zacum = Zsort.cumsum()
    levels = [Zsort[np.where(Zacum > 1 - percent)[0][0]] for percent in percents]

    Z = Z.reshape(X.shape)

    style = {'colors': [colorGmm] * len(percents), 'linestyles': ['dotted', 'dashed','solid']}

    CS = ax1.contour(X, Y, Z, levels=levels, **style)

    fmt = {levels[i]: f'{percents[i]:.0%}' for i in range(len(levels))}
    ax1.clabel(CS, inline=1, fontsize=14, fmt=fmt)
    
    if fileGMM2:
        CS = ax2.contour(X, Y, Z, levels=levels, **style)
        ax3.clabel(CS, inline=1, fontsize=14, fmt=fmt)
        CS2 = ax3.contour(X2, Y2, Z2, levels=levels, **style2)
        ax2.clabel(CS2, inline=1, fontsize=14, fmt=fmt)
        CS2 = ax4.contour(X2, Y2, Z2, levels=levels, **style2)
        ax4.clabel(CS2, inline=1, fontsize=14, fmt=fmt)
        
    else:  
        plt.title(f'Region coverage predicted by {fileGMM}')
        
    plt.axis('tight')
    plt.axis(limits)
    plt.show()

########################################################################################################
# Main Program
########################################################################################################

USAGE='''
Draws the regions in space covered with a certain probability by a GMM.

Usage:
    plotGMM [--help|-h] [options] <file-gmm1> [<file-feat1>...] 
    plotGMM [--help|-h] [options] <file-gmm1> <file-feat1>... [+ <file-feat2>...] [--gmm2 <file-gmm2>] 

Options:
    --xDim INT, -x INT               'x' dimension to use from GMM and feature vectors [default: 0]
    --yDim INT, -y INT               'y' dimension to use from GMM and feature vectors [default: 1]
    --percents FLOAT..., -p FLOAT...  Percentages covered by the regions [default: 90,50]
    --colorGMM STR, -g STR            Color of the GMM regions boundaries [default: firebrick]
    --colorGMM2 STR, -g STR           Color of the GMM regions boundaries [default: darkslateblue]
    --colorFEAT STR, -f STR           Color of the feature population [default: indianred]
    --colorFEAT2 STR, -f STR          Color of the second feature population [default: slateblue]
    --limits xyLimits -l xyLimits     xyLimits are the four values xMin,xMax,yMin,yMax [default: auto]
    --help, -h                        Shows this message
    --gmm2 STR, g STR                 Enable 4 subplots by adding another gmm and set of features


Arguments:
    <file-gmm1>    First file with the Gaussian mixture model to be plotted
    <file-feat1>   First batch of feature files to be plotted along the GMM

'''

if __name__ == '__main__':
    args = docopt(USAGE)


    fileGMM = args['<file-gmm1>']
    filesFeat = args['<file-feat1>']
    fileGMM2= args['--gmm2']

    if fileGMM2!=None:
        filesFeatString = filesFeat[:]
        index = filesFeatString.index("+")
        filesFeat2 = filesFeatString[index+1:len(filesFeatString)]
        filesFeat = filesFeatString[:index]
    else:
        filesFeat2 = None

    xDim = int(args['--xDim'])
    yDim = int(args['--yDim'])
    percents = args['--percents']
    if percents:
        percents = percents.split(',')
        percents = np.array([float(percent) / 100 for percent in percents])
    colorGmm = args['--colorGMM']
    colorGmm2 = args['--colorGMM2']
    colorFeat = args['--colorFEAT']
    colorFeat2 = args['--colorFEAT2']
    limits = args['--limits']
    if limits != 'auto':
        limits = [float(limit) for limit in limits.split(',')]
        if len(limits) != 4:
            print('ERROR: xyLimits must be four comma-separated values')
            exit(1)
    else:
        limits = None

    plotGMM(fileGMM, xDim, yDim, percents, colorGmm, colorGmm2, filesFeat, fileGMM2, filesFeat2, colorFeat, colorFeat2, limits)

