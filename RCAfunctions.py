#############################################################################
# REVERSE CLASSIFICATION ACCURACY IMPLEMENTATION - 2018                     #
# Rob Robinson (r.robinson16@imperial.ac.uk)                                #
# - Includes RCA.py and RCAfunctions.py 				    				#
#                                                                           #
# Original RCA paper by V. Valindria https://arxiv.org/abs/1702.03407       #
# This implementation written by R. Robinson https://goo.gl/NBmr9G          #
#############################################################################

from __future__ import print_function
from __future__ import division

import SimpleITK as sitk
import sys
import time
import os
import numpy as np
import subprocess

from scipy.ndimage import morphology

def dice(A, B):
	### Function to compute the Dice Similarity Coefficient (DSC) between two images ###
	### Inputs:
	### A, B 	= n-Dimensional numpy array
	### Returns - DSC beween A and B (float)
    intersection = np.logical_and(A, B)
    return 2.0 * intersection.sum() / (A.sum() + B.sum())  

def surfd(input1, input2, sampling=1, connectivity=1):
	### Function to compute the surface distance between two binary images ###
	### Inputs:
	### input1, input 2	= n-Dimensional numpy array
	### sampling		= pixel-distance between samples. Variable for morphology.distance_transform_edt
	### connectivity 	= number of neighbours for the morphology.binary_struction and binary_erosion functions
	### Returns - n-Dimensional array showing the surface distance from B to A    
	input_1 	= np.atleast_1d(input1.astype(np.bool))
	input_2 	= np.atleast_1d(input2.astype(np.bool))

	connnect 	= morphology.generate_binary_structure(input_1.ndim, connectivity)

	input1_border 	= np.bitwise_xor(input_1, morphology.binary_erosion(input_1, connnect))
	input2_border 	= np.bitwise_xor(input_2, morphology.binary_erosion(input_2, connnect))

	dta 	  	= morphology.distance_transform_edt(~input1_border,sampling)
	dtb 	  	= morphology.distance_transform_edt(~input2_border,sampling)

	sds 	  	= np.concatenate([np.ravel(dta[input2_border!=0]), np.ravel(dtb[input1_border!=0])])

	return sds


def registration(subject_folder, output_folder, imgFilename, segFilename, maxreferences=100, refdir='./reference_images', classes=[0,1,2,4], doBoth=1):
	### Function to perform registration between N-reference images (+ segmentations) and a single fixed image ###
	### Inputs:
	### subject_folder	= the directory containing the fixed image
	### output_folder	= the directory to store the output
	### imgfilename 	= the filename of the fixed image
	### segFilename 	= the filename of the fixed segmentation
	### maxreferences 	= the number of reference images to register
	### refdir		= the directory containing all reference subjects (each in their own directories)
	### classes 		= the class numbers for the reference images (for the analysis)
	### Returns - a dictionary of data with fields: Image_ID, classes + one field per reference image
	newoutput_folder = os.path.join(output_folder, 'RCA', 'test', 'warped_imgs')
	if not os.path.exists(newoutput_folder):
		os.makedirs(newoutput_folder)
	output_folder = os.path.join(output_folder, 'RCA')

	folders = sorted(os.listdir(refdir))[:maxreferences]

	refs 	= [os.path.join(refdir, f, 'lvsa_ED.nii.gz') for f in folders]
	segs 	= [os.path.join(refdir, f, 'segmentation_ED.nii.gz') for f in folders]

	subject_name 		= os.path.basename(subject_folder)
	subject_image 		= os.path.join(subject_folder, imgFilename)
	subject_seg 		= os.path.join(subject_folder, segFilename)
	fixed_image_img		= sitk.ReadImage(subject_image, sitk.sitkFloat32)
	fixed_image_seg		= sitk.ReadImage(subject_seg, sitk.sitkFloat32)

	elastixImagefilter = sitk.ElastixImageFilter()
	elastixImagefilter.SetOutputDirectory(output_folder)
	elastixImagefilter.LogToConsoleOff()

	parameterMap_1 = elastixImagefilter.GetDefaultParameterMap('rigid')
	parameterMap_1['Transform']					= ['EulerTransform']
	parameterMap_1['AutomaticTransformInitialization'] 		= ["true"]
	parameterMap_1['AutomaticTransformInitializationMethod'] 	= ["CenterOfGravity"]
	parameterMap_1['HowToCombineTransforms'] 			= ['Compose']
	parameterMap_1['WriteResultImage'] 				= ['true']
	parameterMap_1['UseDirectionCosines'] 				= ['true']
	parameterMap_1['Interpolator'] 					= ['LinearInterpolator']
	parameterMap_1['ResampleInterpolator'] 				= ['FinalLinearInterpolator']

	parameterMap = elastixImagefilter.GetDefaultParameterMap('affine')
	parameterMap['Registration'] 					= ['MultiResolutionRegistration']
	#parameterMap['AutomaticTransformInitialization'] 		= ["true"]
	#parameterMap['AutomaticTransformInitializationMethod'] 	= ["CenterOfGravity"]
	parameterMap['Resampler'] 					= ['DefaultResampler']
	parameterMap['WriteResultImage'] 				= ['true']
	parameterMap['UseDirectionCosines'] 				= ['true']
	parameterMap['Interpolator'] 					= ['LinearInterpolator']
	parameterMap['ResampleInterpolator'] 				= ['FinalLinearInterpolator']
	parameterMap['FixedImagePyramid'] 				= ['FixedSmoothingImagePyramid']
	parameterMap['MovingImagePyramid'] 				= ['MovingSmoothingImagePyramid']
	parameterMap['Optimizer'] 					= ['AdaptiveStochasticGradientDescent']
	parameterMap['Transform'] 					= ['BSplineTransform']
	parameterMap['Metric'] 						= ['AdvancedMattesMutualInformation']
	parameterMap['FinalGridSpacingInPhysicalUnits'] 		= ['16']
	parameterMap['GridSpacingSchedule'] 				= ['4.0', '2.0']
	parameterMap['NumberOfResolutions'] 				= ['2']
	parameterMap['ImagePyramidSchedule'] 				= ['4 4 2',  '2 2 2']
	parameterMap['NumberOfSpatialSamples'] 				= ['1024'] #512 in 2D 2048 in 3D
	parameterMap['HowToCombineTransforms'] 				= ['Compose']

	"""MultiMetric"""
	#parameterMap['Registration']						= ['MultiMetricMultiResolutionRegistration']
	#parameterMap['Metric'] 						= ['AdvancedMattesMutualInformation', 'DisplacementMagnitudePenalty']
	#parameterMap['Metric0Weight ']						= ['0.7']
	#parameterMap['Metric1Weight ']						= ['0.3']
	#parameterMap['AutomaticScalesEstimation'] 				= ['true']

	"""Other Parameters"""
	#parameterMap['MaximumNumberOfIterations'] 				= ['500']
	#parameterMap['ResultImagePixelType'] 					= ['short']
	#parameterMap['ResultImageFormat'] 					= ['mhd']
	#parameterMap['NumberOfHistogramBins'] 					= ['32']
	#parameterMap['ErodeMask'] 						= ['false']
	#parameterMap['NewSamplesEveryIteration'] 				= ['true']
	#parameterMap['ImageSampler'] 						= ['Random']
	#parameterMap['BSplineInterpolationOrder'] 				= ['3']
	#parameterMap['FinalBSplineInterpolationOrder'] 			= ['3']
	#parameterMap['DefaultPixelValue'] 					= ['0']
	parameterMapVector = sitk.VectorOfParameterMap()
	parameterMapVector.append(parameterMap_1)
	parameterMapVector.append(parameterMap)

	progress_width=50
	sys.stdout.write("RCA on {} with {} References\t\t\t{}\t{}\t{}\t{}\n".format(subject_name, len(refs), 'DSC', 'MSD', 'RMS', 'HD'))
	sys.stdout.flush()

	Data = []

	for idx, img in enumerate(refs):

		progress_done = int(progress_width*float(idx+1)/len(refs))
		progress_todo = int(progress_width-progress_done)
		if idx >0:
			sys.stdout.write('\r')
			sys.stdout.write('[' + '>'*(progress_done) + 'R' + '-'*(progress_todo) + ']\t'  \
				'{:3.3f}\t{:3.3f}\t{:3.3f}\t{:3.3f}'.format(Data[-1][1][-1], Data[-1][2][-1], Data[-1][3][-1], Data[-1][4][-1]))
			sys.stdout.flush()
		else:
			sys.stdout.write('[' + '>'*(progress_done) + 'R' + '-'*(progress_todo) + ']')
			sys.stdout.flush()

		elastixImagefilter.SetFixedImage(fixed_image_img)
		elastixImagefilter.SetMovingImage(sitk.ReadImage(img))

		if doBoth:
			elastixImagefilter.SetParameterMap(parameterMapVector)
		else:
			elastixImagefilter.SetParameterMap(parameterMap_1)

		try:
			result = elastixImagefilter.Execute()
    		except (KeyboardInterrupt, SystemExit):
        		raise
    		except:
    			sys.stdout.write('\nSimpleElastix error\n')

		sitk.WriteImage(result, '{}/test/warped_imgs/{}_to_{}.nii.gz'.format(output_folder, folders[idx], subject_name))
		
		# old=u'(ResampleInterpolator "FinalLinearInterpolator")'
		# new=u'(ResampleInterpolator "FinalNearestNeighborInterpolator")'

		# mod=[]

		# with open(output_folder+'/TransformParameters.0.txt', "r") as f:
		# 	for line in f:
		# 		if old in line:
		# 			mod.append(new)
		# 		else:
		# 			mod.append(line)
		
		# with open(output_folder+'/TransformParameters.0.txt', "w") as f:
		# 	for m in mod:
		# 		f.write(str(m))


		transformixImageFilter = sitk.TransformixImageFilter()

		transformixPMap_rigid = sitk.ReadParameterFile(output_folder+'/TransformParameters.0.txt')
		transformixPMap_rigid['ResampleInterpolator']	=	["FinalNearestNeighborInterpolator"]
		transformixImageFilter.AddTransformParameterMap(transformixPMap_rigid)

		if doBoth:
			transformixPMap_nonrigid = sitk.ReadParameterFile(output_folder+'/TransformParameters.1.txt')
			transformixPMap_nonrigid['ResampleInterpolator']	=	["FinalNearestNeighborInterpolator"]		
			transformixImageFilter.AddTransformParameterMap(transformixPMap_nonrigid)

		transformixImageFilter.SetMovingImage(sitk.ReadImage(segs[idx]))

		transformixImageFilter.LogToConsoleOff()
		try:
			result = transformixImageFilter.Execute()
     		except (KeyboardInterrupt, SystemExit):
        		raise
 		except:
    			sys.stdout.write('\nTransformix error\n')


	    	sitk.WriteImage(result, '{}/test/{}_to_{}seg.nii.gz'.format(output_folder, folders[idx], subject_name))
	    	os.rename(output_folder+'/TransformParameters.0.txt', '{}/TransformParameters.{}_to_{}.txt'.format(output_folder, folders[idx], subject_name))

	    	ref_map = sitk.GetArrayFromImage(result)
	    	subject_map = sitk.GetArrayFromImage(fixed_image_seg)

	 # 	thisimg 	= '{}/test/{}_to_{}seg.nii.gz'.format(output_folder, folders[idx], subject_name)
		# ref_map 	= sitk.GetArrayFromImage(sitk.ReadImage(thisimg))
	 # 	subject_map 	= sitk.GetArrayFromImage(fixed_image_seg)

	    	try:
	    		Data.append([folders[idx]] + getMetrics(subject_map, ref_map, subject_classes=classes))
    		except (KeyboardInterrupt, SystemExit):
        		raise
    		except:
    			sys.stdout.write('\nMetric error\n')
		#time.sleep(0.1)

	sys.stdout.write('\r')
	sys.stdout.write('[' + '='*(progress_width+1) + ']\n\n')
	sys.stdout.flush()

	return Data

def getMetrics(subject_seg, ref_seg, subject_classes=[0,1,2,3], ref_classes=[0,1,2,4]):
	### Function to assemble the metrics between a reference segmentation and fixed segmentation ###
	### Inputs:
	### subject_seg, ref_seg = n-Dimensional numpy array
	### subject_classes      = the class numbers for the fixed iamge
	### ref_classes 	 = the class numbers for the reference iamge
	### Returns - an array of metrics [Dice, MSD, RMS and HD]
	### MSD = mean surface distance, RMD = root mean-square surface distance and HD = Hausdorff distance 
	    	thisDSC = []
	    	thisMSD = []
	    	thisRMS = []
	    	thisHD  = []
	    	for subject_label, ref_label in zip(subject_classes, ref_classes):
			surface_distance = surfd(subject_seg==subject_label, ref_seg==ref_label)
			thisDSC.append(	dice(    subject_seg==subject_label, ref_seg==ref_label))
			thisMSD.append(	surface_distance.mean())
			thisRMS.append(	np.sqrt((surface_distance**2).mean()))
			thisHD.append(	surface_distance.max())
    		surface_distance = surfd(subject_seg, ref_seg)
		thisMSD.append(	surface_distance.mean())
		thisRMS.append(	np.sqrt((surface_distance**2).mean()))
		thisHD.append(	surface_distance.max())
		thisDSC.append(dice(subject_seg>0, ref_seg>0))
		#thisDSC.append(np.mean(thisDSC))

	    	return [thisDSC, thisMSD, thisRMS, thisHD]
