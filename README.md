# RCA
### Implementation of Reverse Classification Accuracy in Python with SimpleElastix

This code implements Reverse Classification Accuracy (RCA) as applied in our MICCAI 2017 paper:

Robinson, R., Valindria, V.V., Bai, W., Suzuki, H., Matthews, P.M., Page, C., Rueckert, D., Glocker, B.: Automatic Quality Control of Cardiac MRI Segmentation in Large-Scale Population Imaging. In Descoteaux, M., Maier-Hein, L., Franz, A., Jannin, P., Collins, D.L., Duchesne, S., eds.: Medical Image Computing and Computer Assisted Intervention - MICCAI 2017, Cham, Springer International Publishing (2017) 720–727

https://www.springerprofessional.de/en/automatic-quality-control-of-cardiac-mri-segmentation-in-large-s/14978904

RCA predicts the quality of a set of image-segmentations using Reverse Classificaion Accuracy (RCA). The original paper on RCA is:

Valindria, V. V, Lavdas, I., Bai, W., Kamnitsas, K., Aboagye, E. O., Rockall, A. G., … Glocker, B. (2017). Reverse Classification Accuracy: Predicting Segmentation Performance in the Absence of Ground Truth. IEEE Transactions on Medical Imaging, 1–1. [https://doi.org/10.1109/TMI.2017.2665165](https://doi.org/10.1109/TMI.2017.2665165 'RCA Paper')

## Requirements

These scripts use SimpleElastix to perform image registration. This must be compiled *at the same time* as SimpleITK and can casue some issues if the install is not clean. We recommend creating a new virtualenv and following the documentation here: [http://simpleelastix.readthedocs.io/GettingStarted.html](http://simpleelastix.readthedocs.io/GettingStarted.html 'SimpleElastix'). We also use `nibabel` for some loading functions. The requirements.txt is:

```
nibabel==2.2.0
numpy==1.14.2
scipy==1.0.1
SimpleITK==1.1.0
```

To run RCA on an image-segmentation pair, you require a small set of reference images (there are 5 in our demo below, but we use 100 in practice) and corresponding manual segmentations that are representative of the domain of your segmentation-under-test e.g. a set of short-axis cardiac MRI atlases for testing a short-axis cardiac MRI segmentation.

There are three files:
* `RCA.py` - the script run to evaluate the predicted quality of a segmentation (see usage below)
* `RCAfunctions.py` - helper functions for data input, image registration and evaluation
* `config.cfg` - a configuration file containing important variables

## Output

The output is two-fold

* a visual representation on-screen showing the distribution of reference images by DSC along with the overall output of best DSC and surface-distance metrics. The atlas (reference image) that contributed the score is also shown e.g. `Atlas: 0`
* a `.mat` file in `output_folder/data` which contains the DSC and surface distance metrics per class and for the whole-segmentation case for each reference image. i.e. each reference image gets a `n x 5` matrix of metric values where `n` is the number of classes. The overall prediction is also stored in the `.mat`.

## Usage

`python ./RCA.py --subject/subjects subjects.txt --refs ./refs --config SOMENAME --GT filename.nii.gz --seg filename.nii.gz --output ./done`

* `--subject`: a directory containing the image and segmentation to be tested; OR
* `--subjects`: a `.txt` file containing one image-folder path per line;
* `--refs`: a directory containing subfolders, one for each reference image-segmentation pair;
* `--config`: name of the config file that contains the filenames;
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

The configuration file named `config.cfg` is passed to the script. This allows distinction between different experiments using different filenames. You must supply `image_FILE` and `seg_FILE` along with the class-labels in `.cfg` e.g.:

```
image_FILE = "image.nii.gz"
seg_FILE = "segmentation.nii.gz"
class_list = [0,1,2,4]
```

## Demo

You will need to clone this repository and also download two folders into its root:

* `reference_images`: a set of 5 reference images and manual segmentations [available here](https://www.doc.ic.ac.uk/~rdr16/RCA/reference_images/ 'reference_images')
* `test_subjects`: a single folder containing the automated segmentation `segmentation.nii.gz` of an image `image.nii.gz` and its manual `GT.nii.gz` [available here](https://www.doc.ic.ac.uk/~rdr16/RCA/test_subjects/ 'test_subjects')

We have classes 0 (background), 1 (LV cavity), 2 (LV myocardium) and 4 (RV cavity) in our segmentations, so the `config.cfg` is the same as the one in this repository.

### For a single test-segmentation:

We pass the name of the directory that contains all of the files associated with the test-segmentation we want to test. We can run the command:

```
python ./RCA.py --subject ./test_subjects/subject1 --refs ./reference_images --config config.cfg --GT GT.nii.gz --seg segmentation.nii.gz --output ./done
```

This runs RCA on the single subject `subject1` and places the output into a folder called `done`.

### For a selection of test-segmentations

 If we pass a `.txt` containing a list of the directories for subjects 1-`n`, we would have `n` subfolders for each subject placed into `done`. We create `test_subjects.txt` that contains:

```
./test_subjects/subject1
./test_subjects/subject2
```

This time we pass the argument `subjects` and not `subject`:

```
python ./RCA.py --subjects test_subjects.txt --refs ./reference_images --config config.cfg --GT GT.nii.gz --seg segmentation.nii.gz --output ./done
```

## Contact

Questions and comments can be directed to Rob Robinson: r.robinson16@imperial.ac.uk

Cite the MICCAI 2017 paper if using/modifying this code:

Robinson, R., Valindria, V.V., Bai, W., Suzuki, H., Matthews, P.M., Page, C., Rueckert, D., Glocker, B.: Automatic Quality Control of Cardiac MRI Segmentation in Large-Scale Population Imaging. In Descoteaux, M., Maier-Hein, L., Franz, A., Jannin, P., Collins, D.L., Duchesne, S., eds.: Medical Image Computing and Computer Assisted Intervention - MICCAI 2017, Cham, Springer International Publishing (2017) 720–727

https://www.springerprofessional.de/en/automatic-quality-control-of-cardiac-mri-segmentation-in-large-s/14978904