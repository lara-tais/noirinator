#Noir-Inator: a script to process individual Blender output images into a
#vectorized high-contrast single-file starting point for a comic book scene in SVG
#It responds to a very personal workflow and was intended for my own use
#Configuration in accompanying XML file, execution starts in line 96
import xml.etree.ElementTree as etree
from PIL import Image
from potrace import Bitmap
import os
import numpy

def load_settings():
    # Loads config from old XML file
    # TODO: Rewrite to CONST file
    settingsXML = etree.parse('noirinator.xml').getroot()
    settings = {}
    for element in settingsXML:
        settings[element.tag] = element.text
    return settings


def bmp_preprocess(file, maxWidth = 1200):
    # Optimizes the Blender output for tracing using PIL
    # by converting to grayscale and adjusting size if needed
    image = Image.open(file)
    width = image.size[0]
    image = image.convert('L')
    if width > maxWidth:
        image.thumbnail((maxWidth,maxWidth), Image.ANTIALIAS);
    image.save(file)


def bmp_trace(image, steps = 8):
    bmp = numpy.asarray(Image.open(image))
    path = bmp.trace()
    # Tracing similar to the Inkscape "brightness steps" option using potrace
    # Output is a set of SVG files containing original image plus raw tracing
    return path


def svg_postprocess(file, ns, background = 1, whiteLevels = 4):
    # Postprocesses the trace, removing the original image and the background
    # Removes shades to turn grayscale into black and white

    document = etree.parse(file)
    svg = document.getroot()

    layer = svg.find(ns + 'g') # Find main layer
    image = layer.find(ns + 'image')
    layer.remove(image) #remove original image from layer
    group = layer.find(ns + 'g') # Identify relevant path group

    # Delete number of background paths set in config
    for i in range(0,background):
        path = group.find(ns + 'path')
        group.remove(path)

    # Turn grayscale into black and white
    # Non-destructive, paths are not deleted but colored
    for counter, path in enumerate(group):
        if counter <= whiteLevels:
            path.set('style', "fill:#ffffff;fill-opacity:1")
        else:
            path.set('style', "fill:#000000;fill-opacity:1")
    return group


def prepare_svg_canvas():
    settings = load_settings()
    master_svg = etree.parse('master.svg');
    master_layer = master_svg.getroot().find(settings['xmlNamespace'] + 'g')

    for file in os.listdir(settings['inputDir']):
        if file.lower().endswith(".jpg"):
            print('Processing file: ' + file)
            jpg_file = settings['inputDir'] + '/' + file
            svg_file = settings['processDir'] + '/' + file[:-3] + 'svg'
            bmp_preprocess(jpg_file, int(settings['imgMaxSize']))
            bmp_trace(jpg_file, int(settings['steps']))
            path = svg_postprocess(svg_file,
                    settings['xmlNamespace'],
                    int(settings['backgroundSteps']),
                    int(settings['steps']) - int(settings['backgroundSteps']) - int(settings['blackSteps']) )
            master_layer.append(path)

    master_svg.write('master.svg')
    print('SVG canvas ready.')


prepare_svg_canvas()
