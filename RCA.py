#############################################################################
# REVERSE CLASSIFICATION ACCURACY IMPLEMENTATION - 2018                     #
# Rob Robinson (r.robinson16@imperial.ac.uk)                                #
# - Includes RCA.py and RCAfunctions.py                                     #
#                                                                           #
# Original RCA paper by V. Valindria https://arxiv.org/abs/1702.03407       #
# This implementation written by R. Robinson https://goo.gl/NBmr9G          #
#############################################################################

import os
import sys
import subprocess
import shutil
import numpy as np
from scipy import io as scio
import nibabel as nib
from RCAfunctions import registration, getMetrics

import SimpleITK as sitk
import time
import argparse
import scipy.io


G  = '\033[32m'
W  = '\033[0m'
R  = '\033[31m'

############################################################################################################################
######################################### PARSE ARGUMENTS ##################################################################

prog_help = "Script must be given (--refs, --subject, --config, --output\n"\
           "--refs                  = directory where reference images are listed (pre-prepared)\n"\
           "--subject               = directory containing the image, segmentation and landmarks to be tested\n"\
           "--subjects              = .txt file containing one subject-folder path per line\n"\
           "--config                = '5kBIOBANK', 'ATLAS' or 'BIOBANK'\n"\
           "--GT                    = the filename of the GT segmentation (optional)\n"\
           "--seg                   = the filename of the test segmentation (optional)\n"\
           "--output                = root folder to output the files (option - default to pwd)\n"

parser = argparse.ArgumentParser(description='Perform RCA on [subject] using a set of [reference images]')
parser.add_argument('--refs', type=str, default='/vol/biomedic/users/rdr16/RCA2017/registeredCropped')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--subject', type=str)
group.add_argument('--subjects', type=str)
parser.add_argument('--config', type=str, default='5kBIOBANK')
parser.add_argument('--output', type=str)  
parser.add_argument('--GT', type=str, default=False)
parser.add_argument('--seg', type=str, default=False)
parser.add_argument('--prep', type=str, default=False)
args = parser.parse_args()

#####   OUTPUT FOLDERS #####
# This is the *root* of the output
if not args.output:
    output_root = os.getcwd()
else:
    output_root = args.output

#####   SUBJECT FOLDERS #####
# If a list of subjects is given, read them in and assign corresponding outputs (becomes, output_FOLDER/RCA. Default pwd/RCA)
# If a single subject is given, put it in a list (to be read by for loop) and assign the output_FOLDER as given
if args.subjects:
    subjectList = []
    outputList  = []
    with open(args.subjects, 'r') as subjects:
        subjectList = subjects.read().splitlines()
    for line in subjectList:
        outputList.append(os.path.join(output_root, 'RCA2964_2D', os.path.basename(line)))
else:
    subjectList = [args.subject] # list so that single subject can enter for-loop
    if not os.path.exists(os.path.abspath(output_root)):
        os.makedirs(os.path.abspath(output_root))
    output_FOLDER = os.path.abspath(output_root)
    print G+'[*] output_folder: \t\t{}'.format(output_FOLDER)+W
    outputList = [output_FOLDER]


##### BEGIN FOR LOOP OVER ALL SUBJECTS (OR SINGLE SUBJECT) #####
for subject, output_FOLDER in zip(subjectList, outputList): 
    t0 = time.time()

#####   CHECK: DOES THE SUBJECT EXIST?   #####
    if not os.path.isdir(os.path.abspath(subject)):
        msg = R+"[*] Subject folder doesn't exist: {}\n\n".format(subject)+W
        sys.stdout.write(msg + prog_help)
        continue
    else:
        subject_FOLDER = os.path.abspath(subject)
        subject_NAME = os.path.basename(subject_FOLDER) 
        print G+'[*] subject_name: \t\t{}'.format(subject_NAME)+W
        print G+'[*] subject_folder: \t\t{}'.format(subject_FOLDER)+W


#####   CHECK: HAS RCA ALREADY BEEN PERFORMED?  #####
# If there's already a data-file or an exception folder - skip this subject
# Otherwise, check if any new files are being created (i.e. RCA in process)
    datafile = os.path.join(output_FOLDER, 'data', '{}.mat'.format(subject_NAME))
    if os.path.exists(datafile) or os.path.exists(os.path.join(output_FOLDER, 'exception')):
        continue 
    elif os.path.exists(os.path.join(output_FOLDER, 'RCA', 'test')):
        if not os.path.exists(datafile) and os.listdir(os.path.join(output_FOLDER, 'RCA', 'test')):
            f1 = os.path.getmtime(os.path.join(output_FOLDER, 'RCA', 'test', os.listdir(os.path.join(output_FOLDER, 'RCA', 'test'))[-1]))
            time.sleep(10)
            f2 = os.path.getmtime(os.path.join(output_FOLDER, 'RCA', 'test', os.listdir(os.path.join(output_FOLDER, 'RCA', 'test'))[-1]))
            if f1==f2:
                shutil.rmtree(output_FOLDER)
                sys.stdout.write('Removing incomplete directory: {}\n'.format(output_FOLDER))
            else:
                continue
    os.makedirs(os.path.join(output_FOLDER, 'data'))


#####   CHECK: ARE WE DEALING WITH A GROUND-TRUTH SITUATION?    #####
    if args.GT:
        if not os.path.isfile(os.path.abspath(os.path.join(subject, args.GT))):
            msg = R+"[*] Subject GT file doesn't exist: {}\n\n".format(os.path.abspath(os.path.join(subject, args.GT)))+W
            sys.exit(msg + prog_help)
        else:
            subject_GT_FILE = os.path.abspath(os.path.join(subject, args.GT))
            print G+'[*] subject_GT: \t\t{}'.format(os.path.abspath(os.path.join(subject, args.GT)))+W


#####   CHECK: DO THE REFERENCE IMAGES EXIST?   #####
    if not os.path.isdir(os.path.abspath(args.refs)):
        msg = R+"[*] Reference image folder doesn't exist: %s\n\n"+W % args.refs
        sys.exit(msg + prog_help)
    else:
        ref_img_FOLDER = os.path.abspath(args.refs)
        print G+'[*] ref_folder: \t\t{}'.format(ref_img_FOLDER)+W   


#####   ASSIGN: VARIABLES BASED ON THE CONFIG FILE  #####
# This line reads in "image_FILE, seg_FILE and landmarks_FILE variables based on args.config"
    if not os.path.exists(os.path.abspath('config_file_filenames_' + args.config + '.cfg')):
        msg = R+"[*] Config file doesn't exist: {}\n\n".format(args.config)+W
        sys.exit(msg + prog_help)
    else:
        filenames_CONFIG = os.path.abspath('config_file_filenames_' + args.config + '.cfg')
        print G+'[*] config_file: \t\t{}'.format(filenames_CONFIG)+W
    image_FILE      = []
    seg_FILE        = []
    landmarks_FILE  = []
    execfile(filenames_CONFIG)

##### ASSIGN: THE CLASS NUMBERS FOR SEGMENTATIONS   #####
    if args.config == '5kBIOBANK':
        class_list = [0,1,2,3]     # Classes in the segmentations 0= Background, 1=LV Cavity, 2=LV Myocardium, 4=RV Cavity (3 in 5kBiobank)
    else:
        class_list = [0,1,2,4]


##### NOTUSED: POTENTIAL TO USE THIS TO CALL AUGMENTATIONS/CROPPING #####
# Defaults to off
    if args.prep:
        print G+'[*] Ref image prep.:\t\tOn' +W
    else:
        print G+'[*] Ref image prep.:\t\t' +R+ 'Off'+W

##### CHECK: DOES THE TEST-SEGMENTATION EXIST?  #####
    if args.seg:
        if not os.path.isfile(os.path.abspath(os.path.join(subject, args.seg))):
            msg = R+"[*] Subject seg file doesn't exist: {}\n\n".format(os.path.abspath(os.path.join(subject, args.seg)))+W
            sys.exit(msg + prog_help)
        else:
            seg_FILE = os.path.abspath(os.path.join(subject, args.seg))
            print G+'[*] subject_seg: \t\t{}'.format(os.path.abspath(os.path.join(subject, args.seg)))+W

#####   ASSIGN: ALL FILES SHOULD NOW BE ACCESSIBLE  #####
# Copy the primary image and segmentation to the RCA folder
    subject_image_FILE     = os.path.abspath(os.path.join(subject_FOLDER, image_FILE        ))
    subject_seg_FILE       = os.path.abspath(os.path.join(subject_FOLDER, seg_FILE          ))
    subject_landmarks_FILE = os.path.abspath(os.path.join(subject_FOLDER, landmarks_FILE    ))

    os.makedirs(os.path.join(output_FOLDER, 'main_image', 'cropped'))
    for f in [subject_image_FILE, subject_seg_FILE]:
        shutil.copy(f, os.path.join(output_FOLDER, 'main_image', 'cropped'))


#########################################################################################################################
###################### BEGIN RCA ANALYSIS ###############################################################################

    print "\nRCA analysis on:\n" \
          "Image:\t\t {}\n" \
          "Segmentation:\t {}".format(subject_image_FILE, subject_seg_FILE)
    if args.GT:
        print "GT Seg.:\t {}\n".format(subject_GT_FILE)
    else:
        sys.stdout.write('\n')

##### Sometimes the segmentation is not the same depth as the image - getMetrics throws IndexError exception
# Best to catch the error and move on to a different subject rather than quit the loop
    try:
        Data = registration(subject_folder = subject_FOLDER, output_folder=output_FOLDER, imgFilename=image_FILE, segFilename=seg_FILE, refdir=args.refs, classes=class_list, doBoth=1)
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        os.makedirs(os.path.join(output_FOLDER, 'exception'))
        continue

# To recalculate GT metrics after RCA ###
    # print datafile
    # Data_ = scipy.io.loadmat(datafile)
    # print G+'[*] Loaded data:\t{}\n'.format(datafile)+W
    # Data=[]
    # for key in Data_.keys():
    #     if key.startswith('Ref'):
    #         Data.append([key.split('Ref')[-1]] + list(Data_[key]))
    # if len(Data)<100:
    #     print R+'################ {} ##############'.format(subject_image_FILE)+W
    #     continue

##### DISPLAY: OUTPUT SOME VISUALS AND STATISTICS FOR RCA   #####
    DSCs = np.array([data[1] for data in Data])
    MSDs = np.array([data[2] for data in Data])
    RMSs = np.array([data[3] for data in Data])
    HDs = np.array([data[4] for data in Data])

    factor = 1 #to change the length of the distribution graph

    if len(DSCs[:,-1])>=50:
        factor = 2

    sys.stdout.write('RCA DSC Distribution:\n')
    sys.stdout.write('0.0 - 0.1:\t {:3d} {}\n'.format(len(DSCs[np.where( DSCs[:,-1]<0.1)]),'>'*(len(DSCs[np.where( DSCs[:,-1]<0.1)])/factor)))
    sys.stdout.write('0.1 - 0.2:\t {:3d} {}\n'.format(len(DSCs[np.where( (DSCs[:,-1]>=0.1) & (DSCs[:,-1]<0.2) )]), '>'*(len(DSCs[np.where( (DSCs[:,-1]>=0.1) & (DSCs[:,-1]<0.2) )])/factor)))
    sys.stdout.write('0.2 - 0.3:\t {:3d} {}\n'.format(len(DSCs[np.where( (DSCs[:,-1]>=0.2) & (DSCs[:,-1]<0.3) )]), '>'*(len(DSCs[np.where( (DSCs[:,-1]>=0.2) & (DSCs[:,-1]<0.3) )])/factor)))
    sys.stdout.write('0.3 - 0.4:\t {:3d} {}\n'.format(len(DSCs[np.where( (DSCs[:,-1]>=0.3) & (DSCs[:,-1]<0.4) )]), '>'*(len(DSCs[np.where( (DSCs[:,-1]>=0.3) & (DSCs[:,-1]<0.4) )])/factor)))
    sys.stdout.write('0.4 - 0.5:\t {:3d} {}\n'.format(len(DSCs[np.where( (DSCs[:,-1]>=0.4) & (DSCs[:,-1]<0.5) )]), '>'*(len(DSCs[np.where( (DSCs[:,-1]>=0.4) & (DSCs[:,-1]<0.5) )])/factor)))
    sys.stdout.write('0.5 - 0.6:\t {:3d} {}\n'.format(len(DSCs[np.where( (DSCs[:,-1]>=0.5) & (DSCs[:,-1]<0.6) )]), '>'*(len(DSCs[np.where( (DSCs[:,-1]>=0.5) & (DSCs[:,-1]<0.6) )])/factor)))
    sys.stdout.write('0.6 - 0.7:\t {:3d} {}\n'.format(len(DSCs[np.where( (DSCs[:,-1]>=0.6) & (DSCs[:,-1]<0.7) )]), '>'*(len(DSCs[np.where( (DSCs[:,-1]>=0.6) & (DSCs[:,-1]<0.7) )])/factor)))
    sys.stdout.write('0.7 - 0.8:\t {:3d} {}\n'.format(len(DSCs[np.where( (DSCs[:,-1]>=0.7) & (DSCs[:,-1]<0.8) )]), '>'*(len(DSCs[np.where( (DSCs[:,-1]>=0.7) & (DSCs[:,-1]<0.8) )])/factor)))
    sys.stdout.write('0.8 - 0.9:\t {:3d} {}\n'.format(len(DSCs[np.where( (DSCs[:,-1]>=0.8) & (DSCs[:,-1]<0.9) )]), '>'*(len(DSCs[np.where( (DSCs[:,-1]>=0.8) & (DSCs[:,-1]<0.9) )])/factor)))
    sys.stdout.write('0.9 - 1.0:\t {:3d} {}\n\n'.format(len(DSCs[np.where( (DSCs[:,-1]>=0.9) & (DSCs[:,-1]<=1.0))]), '>'*(len(DSCs[np.where( (DSCs[:,-1]>=0.9) & (DSCs[:,-1]<1.0) )])/factor)))
    sys.stdout.flush()

    sys.stdout.write('Predicted DSC:\t{}\tAtlas: {}\n'.format(np.max(DSCs[:,-1]), np.argmax(DSCs[:,-1])))
    sys.stdout.write('Minimum MSD:\t{}\tAtlas: {}\n'.format(np.min(MSDs[:,-1]), np.argmin(MSDs[:,-1])))
    sys.stdout.write('Minimum RMS:\t{}\tAtlas: {}\n'.format(np.min(RMSs[:,-1]), np.argmin(RMSs[:,-1])))
    sys.stdout.write('Minimum HD:\t{}\tAtlas: {}\n\n'.format(np.min(HDs[:,-1]), np.argmin(HDs[:,-1])))


##### OUTPUT: PREPARE THE DATA FOR OUTPUT AND CALCULATE THE GT REAL METRICS IF POSSIBLE    #####
    Datadict = {}
    Datadict['ImageID'] = subject_NAME
    Datadict['Classes'] = class_list

    if args.GT:
        realMetrics = getMetrics(sitk.GetArrayFromImage(sitk.ReadImage(subject_GT_FILE)), sitk.GetArrayFromImage(sitk.ReadImage(subject_seg_FILE)), ref_classes=[0,1,2,4])
        sys.stdout.write('Real DSC: \t{}\n\n'.format(realMetrics[0][-1]))
        sys.stdout.flush()    

    for ref in Data:
        Datadict['Ref{}'.format(ref[0])] = ref[1:]

    RefData = np.array([Datadict[ref] for ref in Datadict.keys() if 'Ref' in ref])
    maxs = [np.max(RefData, axis=0), np.argmax(RefData, axis=0)+1]
    mins = [np.min(RefData, axis=0), np.argmin(RefData, axis=0)+1]
    Datadict['MaxMetrics'] = np.concatenate([np.reshape(np.array(maxs)[:,0,:], [2,1,5]), np.array(mins)[:,1:,:]], axis=1).transpose(1,2,0)

    if args.GT:
        Datadict['GTMetrics'] = realMetrics
    
    scipy.io.savemat(datafile, Datadict)
 
 ##### TIME: CALCULATE AND DISPLAY TIME FOR ANALYSIS    #####
    t1      = time.time()
    elapsed = t1 - t0
    hours = elapsed//3600
    mins = (elapsed-(3600*hours))//60 
    secs = (elapsed-(3600*hours)-(mins*60))
    sys.stdout.write('Elapsed Time: {:02d}h {:02d}m {:02d}s\n\n'.format(int(hours), int(mins), int(secs)))
    sys.stdout.flush()
    #time.sleep(5)

sys.exit(0)