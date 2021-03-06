import sys,os,json,argparse,math
from PIL import Image, ImageDraw

import numpy as np
import cv2
import matplotlib.pyplot as plt
from scipy import stats

import analyzers
from utils import *
from analyzers import *


def pass_rectangles(rects,sides=4):
    filtered = []
    left = []
    for x in rects:
        #print(x['area-ratio'])
        if x['area-ratio'] > 0.001:
            #print(x['conf'])
            if np.sum(x['conf'] > .95) >= sides:
                filtered.append(x)
            else:
                left.append(x)
        else:
            left.append(x)
    return filtered,left

def pass_semi_rectangles(rects):
    filtered = []
    left = []
    for x in rects:
        #print(x['area-ratio'])
        if x['area-ratio'] > 0.001:
            bad = False
            for i in range(0,4):
                if x['conf'][i] < .95 and x['semi-circles'][i][2]<.45:
                    bad = True
                    break

            #print(x['conf'])
            if not bad: #(.49 for half a circle)
                filtered.append(x)
            else:
                left.append(x)
        else:
            left.append(x)
    return filtered,left


def pass_potential_rectangles(rects):
    filtered = []
    left = []
    for x in rects:
        if x['area-ratio'] > 0.001:
            filtered.append(x)
        else:
            left.append(x)
    return filtered,left


def pass_lines(rects):
    lines = []
    leftover = []
    # TODO connect this with `contains_line` to prevent infinite loops
    for x in rects:
        score = x['sum']['score']
        distinct = x['sum']['distinct']


        #if x['aspect-ratio'] > 10:
            #lines.append(x)
        if (x['aspect-ratio'] > 1.1) and (score > .7) and (distinct < 3):
            lines.append(x)
        else:
            leftover.append(x)
    return lines,leftover

def contains_line(spec):
    s = spec['sum']
    return s['mode'][0] and (len(s['sum'])/s['mode'][0] > 15)

def pass_potential_lines(inp):
    lines = []
    nolines = []
    for x in inp:
        if contains_line(x):
            lines.append(x)
        else:
            nolines.append(x)
    return lines,nolines

def block_dots(fresh):
    good = []
    for x in fresh:
        nz = np.count_nonzero(x['img'])
        z = x['img'].shape[0] * x['img'].shape[1] - nz
        if z > 1:
            good.append(x)
    return good

def triangle_passes(x):
    dim = min(analyzers.PARAMS['imageh'],analyzers.PARAMS['imagew'])/2
    return (x['triangle-area-ratio']>.5) and (x['triangle-perimeter'] < dim)

def pass_triangles(inp, bim = None):
    tris = []
    notris = []
    #dim = min(analyzers.PARAMS['imageh'],analyzers.PARAMS['imagew'])/2
    for x in inp:
        if triangle_passes(x):
            tris.append(x)
        else:
            notris.append(x)

    return tris,notris

def pass_ocr(inp):
    good = []
    bad = []
    for x in inp:
        if x['ocr-conf'] >= 60:
            good.append(x)
        else:
            bad.append(x)
    return good,bad

def pass_slashes(inp):
    slash =[]
    nope = []
    for x in inp:
        if x['symbol'] in '/\\':
            slash.append(x)
        else:
            nope.append(x)
    return slash,nope

def count_black_circle(im,c):
    #newim = np.zeros(im.shape,dtype=np.uint8) + 255
    mask = np.zeros(im.shape,dtype=np.uint8)
    cv2.fillPoly(mask, [c], color=255, lineType=4)
    return count_black(0==((im==0) & mask))
    

def pass_circles(inp):
    good = []
    bad = []
    for x in inp:
        #print(x['circle'])
        area = x['circle'][1]**2 * math.pi
        if x['circle-conf'] > .94 and (x['circle'][1] > 4) and (count_black_circle(x['img'], x['circle-contour'])/area < .9):
            #and (count_black_circle(x['img'], x['circle-contour'])/area < .5):
            #print( count_black_circle(x['img'], x['circle-contour']),area)
            good.append(x)
        else:
            bad.append(x)
    return good,bad

def pass_irregs(irregs):
    good = []
    notgood = []
    for x in irregs:
        bad = False
        for f in x['features']:
            if f[0] == 'line':
                if f[3] < .95:
                    bad = True
            elif f[0] == 'circle':
                if f[3] < .45:
                    bad = True
        if not bad:
            good.append(x)
        else:
            notgood.append(x)
    return good,notgood



if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: %s <input.png>' % sys.argv[0])
        sys.exit(1)

    arr = load_image(sys.argv[1])
    dim = 1

    y = scan_dim(arr,dim)
    m = stats.mode(y)
    print('%d occurs %d times (%.2f)' % (m[0][0],m[1][0], float(m[1][0])/len(y) ))
    print(m)


    if (len(y)/m[0][0]) > 10:
        print('It\'s a line!  Extracting..')
        newim,arr = extract(arr,y,m[0][0],dim)
    save(arr,'output1.png')
    save(newim,'output2.png')
    #plt.plot((y==m[0][0]) * 50 + m[0][0])
    #plt.plot(y)
    #plt.show()




