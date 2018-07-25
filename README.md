# RCA
### Implementation of Reverse Classification in Python with SimpleElastix

This code implements Reverse Classification Accuracy (RCA) as applied in our MICCAI 2017 paper:

Robinson, R., Valindria, V.V., Bai, W., Suzuki, H., Matthews, P.M., Page, C., Rueckert, D., Glocker, B.: Automatic Quality Control of Cardiac MRI Segmentation in Large-Scale Population Imaging. In Descoteaux, M., Maier-Hein, L., Franz, A., Jannin, P., Collins, D.L., Duchesne, S., eds.: Medical Image Computing and Computer Assisted Intervention - MICCAI 2017, Cham, Springer International Publishing
(2017) 720–727

https://www.springerprofessional.de/en/automatic-quality-control-of-cardiac-mri-segmentation-in-large-s/14978904

RCA predicts the quality of a set of image-segmentations using Reverse Classificaion Accuracy (RCA). The original paper on RCA is:

Valindria, V. V, Lavdas, I., Bai, W., Kamnitsas, K., Aboagye, E. O., Rockall, A. G., … Glocker, B. (2017). Reverse Classification Accuracy: Predicting Segmentation Performance in the Absence of Ground Truth. IEEE Transactions on Medical Imaging, 1–1. [https://doi.org/10.1109/TMI.2017.2665165](https://doi.org/10.1109/TMI.2017.2665165, 'RCA Paper')

## Requirements

To run RCA on an image-segmentation pair, you require a small (~100) set of reference images and corresponding manual segmentations that are representative of the domain of your segmentation-under-test e.g. a set of short-axis cardiac MRI atlases for testing a short-axis cardiac MRI segmentation.

There are three files:
* `RCA.py` - the script run to evaluate the predicted quality of a segmentation (see usage below)
* `RCAfunctions.py` - helper functions for data input, image registration and evaluation
* `config.cfg` - a configuration file containing important variables

## Usage

`python ./RCA.py --subject/subjects subjects.txt --refs ./refs --config SOMENAME --GT filename.nii.gz --seg filename.nii.gz --output ./done`

* `--subject`: a directory containing the image and segmentation to be tested;
* `--subjects`: a `.txt` file containgin one image-folder path per line;
* `--refs`: a directory containing subfolders, one for each reference image-segmentation pair;
* `--config`: only pass the `SOMENAME` part of the file named `./config_file_filenames_SOMENAME.cfg` file. Contains the filenames;
* `--output`: a directory (will be created) to contain the output from RCA - will create one subfolder per image in `output`;
* `--GT`: (optional) the filename of the ground truth segmentation if we want to evaluate against the real metrics.

### `subject/subjects`

If only a single subject/segmentation is being tested, then only the name of the directory containing the image and segmentation needs to be passed to `--subject` (note this is singular).
For multiple test segmentations, there must be one folder per subject/segmentation containing the image and segmentation to test. A text file containing the path to each of these folders must be passed to `--subjects` (note the plural)

```
|-subjects_folder
  |-subject1
    |-image.nii.gz
    |-segmentation.nii.gz
  |-subject2
    |-image.nii.gz
    |-segmentation.nii.gz
```
The subject names e.g. `subject1` are used to name the output subfolders that will be stored in `output` directory.  A ground truth segmentation can also be present if evaluating the prediction against the real value.


### `refs`

Like the subjects, the reference images and manual segmentations should each be in their own folders. Their parent folder is what is passed to `RCA.py`.

### `config.cfg`

The configuration file is named `./config_file_filenames_SOMENAME.cfg` but only the `SOMENAME` is passed to the script. This allows distinction between different experiments using different filenames. You must supply `image_FILE` and `seg_FILE` in `.cfg`.

```
image_FILE = "sa_ED.nii.gz"
seg_FILE = "label_sa_ED.nii.gz"
```



    



