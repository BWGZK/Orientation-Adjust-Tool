## Cardiac MRI Orientation Adjust Tool

### UI interface

![UI Interface](./data/demo.jpg)


### Command Line Tool

to test folder batch processing, just type:
```
python command.py folder_path -f   
```
to test single file, type: 
```
python command.py file_path  
```

```
usage: command.py file_path
[-h] 
[-k [KEEP_HEADER]] 
[-f [BATCH_PROCESS]]
[-o [SAVE_PATH]] 
[-c [{C0,T2,LGE}]]
```

file_path: the input file path (Required)  

KEEP_HEADER[-k]:  don't ajust the header orientation(Optional)  

BATCH_PROCESS[-f]:  process all files by search the folder(*.mha, *.nii,*.nii.gz are supported) (Optional)  

SAVE_PATH[-o]: specify the save path of adjusted file(Optional)  

TYPE[-c]: specify the type of adjusted file(Optional, [C0,T2,LGE are supported])  

### Citation
Please cite these two works, based on which we trained our DNN models, when you use the tool:  
[1] Xiahai Zhuang: Multivariate mixture model for myocardial segmentation combining multi-source images. IEEE Transactions on Pattern Analysis and Machine Intelligence (T PAMI), vol. 41, no. 12, 2933-2946, Dec 2019.   
[2] Xiahai Zhuang: Multivariate mixture model for cardiac segmentation from multi-sequence MRI.  International Conference on Medical Image Computing and Computer-Assisted Intervention, pp.581-588, 2016. 
