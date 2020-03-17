'''
'''
from PIL import Image
import numpy as np

from tqdm import tqdm

def video_buffer(video_file, nimages=np.inf):
    '''Generator for a video file.

    Yields individual uint8 images from a video file.

    Parameters
    ----------
    video_file : str
        Full path to the video file

    Returns
    -------
    vbuff : generator
        Each ``__next()__`` call yields an RGB frame from video.

    Example
    -------
    >>> image_buffer = video_buffer("myvideo.mp4")               # doctest: +SKIP
    >>> movie = np.asarray([frame for frame in in image_buffer]) # doctest: +SKIP
    '''
    import cv2
    cap = cv2.VideoCapture(video_file)
    frameidx = 0
    while True:
        if frameidx >= nimages:
            break
        flag, im = cap.read()
        frameidx += 1
        if flag:
            yield im[...,::-1] # flip to RGB
        else:
            break


def video2luminance(video_file, size=None, nimages=np.inf):
    '''
    '''
    vbuffer = video_buffer(video_file, nimages=nimages)
    luminance_video = []

    from moten.progress_bar import bar
    for imageidx, image_rgb in tqdm(enumerate(vbuffer), '%s.video2luminance'%__name__):
        luminance_image = imagearray2luminance(image_rgb, size=size).squeeze()
        luminance_video.append(luminance_image)
    return np.asarray(luminance_video)



def imagearray2luminance(uint8arr, size=None, filter=Image.ANTIALIAS, dtype=np.float64):
    '''Convert an array of uint8 RGB images to a luminance image

    Parameters
    ----------
    uint8arr : 4D np.ndarray (n, vdim, hdim, rgb)
        The uint8 RGB frames.

    size (optional) : tuple, (vdim, hdim)
        The desired output image size

    filter: to be passed to PIL

    Returns
    -------
    luminance_array = 3D np.ndarray (n, vdim, hdim)
        The luminance image representation (0-100 range)
    '''
    from scipy import misc
    from moten.colorspace import rgb2lab

    if uint8arr.ndim == 3:
        # handle single image case
        uint8arr = np.asarray([uint8arr])

    nimages, vdim, hdim, cdim = uint8arr.shape
    outshape = (nimages, vdim, hdim) if size is None \
        else (nimages, size[0], size[1])

    luminance = np.zeros(outshape, dtype=dtype)
    for imdx in range(nimages):
        im = uint8arr[imdx]
        if size is not None:
            im = Image.fromarray(im)
            im = resize_image(im, size=size, filter=filter)
        im = rgb2lab(im/255.)[...,0]
        luminance[imdx] = im
    return luminance


def resize_image(im, size=(96,96), filter=Image.ANTIALIAS):
    '''Resize an image and return its array representation

    Parameters
    ----------
    im : str, np.ndarray(uint8), or PIL.Image object
        The path to the image, an image array, or a loaded PIL.Image
    size : tuple, (vdim, hdim)
        The desired output image size

    Returns
    -------
    arr : uint8 np.array, (vdim, hdim, 3)
        The resized image array
    '''
    if isinstance(im, str):
        im = Image.open(im)
    elif isinstance(im, np.ndarray):
        im = Image.fromarray(im)
    im.load()

    # flip to PIL.Image convention
    size = size[::-1]
    try:
        im = im._new(im.im.stretch(size, filter))
    except AttributeError:
        # PIL 4.0.0 The stretch function on the core image object has been removed.
        # This used to be for enlarging the image, but has been aliased to resize recently.
        im = im._new(im.im.resize(size, filter))
    im = np.asarray(im)
    return im


def load_image_luminance(image_files, hdim=None, vdim=None, verbose=False,
                         progress_bar=True):
    '''Load a set of RGB images and return its luminance representation

    Parameters
    ----------
    image_files : list-like, (n,)
        A list of file names.
        The images should be in RGB uint8 format
    vdim, hdim : int, optional
        Vertical and horizontal dimensions, respectively.
        If provided the images will be scaled to this size.
    progress_bar : bool
        If True, display a command-line progress-bar.

    Returns
    -------
    arr : 3D np.array (n,vdim,hdim)
        The luminance representation of the images
    '''
    from moten.colorspace import rgb2lab
    from moten.progress_bar import bar

    if (hdim and vdim):
        loader = lambda stim,sz: resize_image(stim,sz)
    else:
        loader = lambda stim,sz: np.asarray(stim)

    stimuli = []

    for fdx, fl in enumerate(bar(image_files, title="load_image_luminance",
                                 use_it=progress_bar)):
        if verbose:
            if fdx % 500 == 1: print(fdx),
        stimulus = Image.open(fl)
        stimulus = loader(stimulus,(vdim,hdim))
        stimulus = rgb2lab(stimulus/255.)[...,0]
        stimuli.append(stimulus)
    return np.asarray(stimuli)
