import torch
import torchvision
from torchvision import transforms
from torch import nn
import os
import torch.utils.data
from d2l import torch as d2l

data_dir = "/home/hongtao2022/hongtao/pj_orient/data"


data_transforms = {
    'train_data_LGE': transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.RandomRotation(10),
        transforms.RandomResizedCrop((256, 256), scale=(0.7, 1), ratio=(0.8, 1.2)),
        transforms.ToTensor()
    ]),
    'valid_data_LGE': transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.RandomRotation(10),
        transforms.RandomResizedCrop((256, 256), scale=(0.7, 1), ratio=(0.8, 1.2)),
        # transforms.Resize((256, 256)),
        transforms.ToTensor()
    ]),
    'test_data_LGE': transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.RandomRotation(10),
        transforms.RandomResizedCrop((256, 256), scale=(0.7, 1), ratio=(0.8, 1.2)),
        # transforms.Resize((256, 256)),
        transforms.ToTensor()
    ])
}


image_datasets = {
    x: torchvision.datasets.ImageFolder(os.path.join(data_dir, x), data_transforms[x])
    for x in ['train_data_LGE', 'valid_data_LGE', 'test_data_LGE']
}

data_loaders = {
    x: torch.utils.data.DataLoader(image_datasets[x], batch_size=8, shuffle=True, num_workers=4)
    for x in ['train_data_LGE', 'valid_data_LGE', 'test_data_LGE']
}


net = nn.Sequential(
    nn.Conv2d(1, 32, kernel_size=3, padding=1),
    nn.BatchNorm2d(32),
    nn.ReLU(),
    nn.MaxPool2d(kernel_size=2, stride=2),
    nn.Conv2d(32, 32, kernel_size=3, padding=1),
    nn.BatchNorm2d(32),
    nn.ReLU(),
    nn.MaxPool2d(kernel_size=2, stride=2),
    nn.Conv2d(32, 64, kernel_size=3, padding=1),
    nn.BatchNorm2d(64),
    nn.ReLU(),
    nn.MaxPool2d(kernel_size=2, stride=2),
    nn.AvgPool2d(kernel_size=2, stride=2),
    nn.Flatten(),
    nn.Linear(64 * 16 * 16, 64), nn.Sigmoid(),
    nn.Linear(64, 8)
)

train_iter = data_loaders['train_data_LGE']
valid_iter = data_loaders['valid_data_LGE']
test_iter = data_loaders['test_data_LGE']

lr = 0.01
num_epochs = 40
d2l.train_ch6(net, train_iter, test_iter, num_epochs, lr, d2l.try_gpu(1))

d2l.plt.show()
# torch.save(net.state_dict(), 'Ori_C0.pth')
