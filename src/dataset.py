import numpy as np
import pandas as pd
import torchvision.transforms as T
from PIL import Image
from torch.utils.data import Dataset

MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)


def build_transform(img_size: int, train: bool):
    t = [T.Resize((img_size, img_size))]
    if train:
        # No horizontal flip: chest anatomy is lateralized (heart on the left),
        # so a flipped CXR is not a realistic sample.
        t += [
            T.RandomAffine(degrees=7, translate=(0.05, 0.05), scale=(0.9, 1.1)),
            T.ColorJitter(brightness=0.2, contrast=0.2),
        ]
    t += [T.ToTensor(), T.Normalize(MEAN, STD)]
    return T.Compose(t)


def load_image(path) -> Image.Image:
    # CXRs are grayscale; replicate to 3 channels for ImageNet-pretrained backbones
    return Image.open(path).convert("L").convert("RGB")


class CXRDataset(Dataset):
    def __init__(self, df: pd.DataFrame, img_size: int, train: bool):
        self.paths = df["path"].tolist()
        self.labels = df["abnormal"].to_numpy(dtype=np.float32)
        self.tf = build_transform(img_size, train)

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, i):
        return self.tf(load_image(self.paths[i])), self.labels[i]
