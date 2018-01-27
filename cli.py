import sys,os,json,argparse
from PIL import Image, ImageDraw

import numpy as np
import cv2

import analyzers
from utils import *
from filters import *
from analyzers import *
from processors import *
import preprocessing


def arguments():
    parser = argparse.ArgumentParser(description='drawing parser',
            epilog='extra annotations: ocontour,brect,rect,line,tri,circle,ocr\n')
    parser.add_argument('input_file')
    parser.add_argument('--all', action='store_true',help='use all features for operation')
    parser.add_argument('--out', action='store_true',help='display outter contours for targets')
    parser.add_argument('--action', action='store',default='display',
            help='specify action to use on output. display[default],binary,redraw,none')
    parser.add_argument('--save-features', action='store_true', dest='save_features',
            help='save features to output files.  Use switches to select which ones.')
    parser.add_argument('-t', action='store_true',help='triangles (for displaying..)')
    parser.add_argument('-r', action='store_true',help='rectangles')
    parser.add_argument('-c', action='store_true',help='circles')
    parser.add_argument('-l', action='store_true',help='lines')
    parser.add_argument('-o', action='store_true',help='OCR')
    parser.add_argument('-x', action='store_true',help='leftovers')

    parser.add_argument('-T', action='store_true',help='triangles (for saving to file..)')
    parser.add_argument('-R', action='store_true',help='rectangles')
    parser.add_argument('-C', action='store_true',help='circles')
    parser.add_argument('-L', action='store_true',help='lines')
    parser.add_argument('-O', action='store_true',help='OCR')
    parser.add_argument('-X', action='store_true',help='leftovers')
    
    parser.add_argument('--bare', action='store_true',help='dont annotate targets')

    parser.add_argument('--save-type', default='large', action='store', dest='save_type',help='small,large,outlined')
    parser.add_argument('--bg', action='store_true', help='use original image as background for --save-type')
    parser.add_argument('-a', action='append', dest='outa',help='extra annotations to add to output image.')
    parser.add_argument('-b', action='append', dest='savea',help='extra annotations to add to output features.')
    parser.add_argument('-A', action='append', dest='botha',help='extra annotations to add to both output features and image.')

    args = parser.parse_args()
    return args

def do_outputs(orig,outs):

    args = arguments()

    print('%d triangles' % len(outs['triangles']))
    print('%d rectangles' % len(outs['rectangles']))
    print('%d OCR' % len(outs['ocr']))
    print('%d lines' % len(outs['lines']))
    print('%d leftover' % len(outs['leftover']))
    for x in outs['leftover']:
        x['type'] = 'leftover'
    for x in outs['rectangles']:
        x['type'] = 'rectangle'
    for x in outs['triangles']:
        x['type'] = 'triangle'
    for x in outs['lines']:
        x['type'] = 'line'
    for x in outs['ocr']:
        x['type'] = 'ocr'
    for x in outs['circles']:
        x['type'] = 'circle'

    def put_thing(im, x, color, offset=None, thickness = 1):
        if offset is not None: offset = tuple(offset)
        cv2.drawContours(im,[x],0,color,thickness, offset=offset)

    def put_features(im, feats):
        for x in feats:
            if x['type'] == 'rectangle':
                put_thing(im, x['rectangle'], [255,0,255], x['offset'])
            elif x['type'] == 'triangle':
                put_thing(im, x['triangle'], [0,0,255], x['offset'])
            elif x['type'] == 'circle':
                off = x['offset']
                xp = off[0] + x['circle'][0][0]
                yp = off[1] + x['circle'][0][1]
                cv2.circle(im,(xp,yp),x['circle'][1],(255,0x8c,0),2 )
            elif x['type'] == 'ocr':
                put_thing(im, x['ocontour'], [0,255,255], x['offset'], 2)
            elif x['type'] == 'line':
                put_thing(im, x['line'], [0,128,0], x['offset'], 2)
            elif x['type'] == 'leftover':
                put_thing(im, x['ocontour'], [255,0,0], x['offset'])
            else:
                raise RuntimeError('Unclassified feature')

    def put_outlines(im, feats):
        for x in feats:
            put_thing(im, x['ocontour'], [255,0,0], x['offset'])


    def save_things(things,bname='im',path='./out'):
        for i,x in enumerate(things):
            n = path +'/' + bname+('%d.png' % (i))
            print('saving ',n)
            save(x,n)

    target_list = []
    if args.t or args.all:
        target_list += outs['triangles']
    if args.r or args.all:
        target_list += outs['rectangles']
    if args.c or args.all:
        target_list += outs['circles']
    if args.l or args.all:
        target_list += outs['lines']
    if args.o or args.all:
        target_list += outs['ocr']
    if args.x or args.all:
        target_list += outs['leftover']


    
    if args.action == 'display':
        pass
    elif args.action == 'binary':
        orig = polarize(orig)
        orig = color(orig)
    elif args.action == 'redraw':
        orig = np.zeros(orig.shape, dtype=np.uint8)+255
        for x in target_list:
            oldim = x['img']
            oj,oi = x['offset']
            for i in range(0,oldim.shape[0]):
                for j in range(0,oldim.shape[1]):
                    v = oldim[i,j]
                    orig[i+oi,j+oj] = v


        pass #TODO

    if args.action != 'none' and not args.bare:
        put_features(orig,target_list)

    if args.out:
        put_outlines(orig,target_list)

    saving_list = []
    if args.T:
        saving_list += outs['triangles']
    if args.R:
        saving_list += outs['rectangles']
    if args.C:
        saving_list += outs['circles']
    if args.L:
        saving_list += outs['lines']
    if args.O:
        saving_list += outs['ocr']
    if args.X:
        saving_list += outs['leftover']

    if args.save_type == 'large' or args.save_type == 'outline':
        bg = np.zeros(orig.shape,dtype=np.uint8)+255
        if args.bg:
            bg = orig
        for x in saving_list:
            newim = np.copy(bg)
            oldim = x['img']
            oj,oi = x['offset']
            for i in range(0,oldim.shape[0]):
                for j in range(0,oldim.shape[1]):
                    #print(oldim)
                    v = oldim[i,j]
                    newim[i+oi,j+oj] = v

            x['img'] = newim
    if args.save_type == 'outline':
        for x in saving_list:
            encircle(x['img'], x['ocontour'], offset=x['offset'])


    if args.save_features:
        if args.T:
            save_things(outs['triangles'], 'tri')
        if args.R:
            save_things(outs['rectangles'], 'r')
        if args.C:
            save_things(outs['circles'], 'cir')
        if args.L:
            save_things(outs['lines'], 'l')
        if args.O:
            save_things(outs['ocr'], 'ocr')
        if args.X:
            save_things(outs['leftover'], 'leftover')


    save(orig,'output.png')

