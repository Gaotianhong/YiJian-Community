# -*- coding: utf-8 -*-
# Copyright 2024 Ant Group Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import torch
from abc import ABC, abstractmethod
from datasets import Dataset
from .model import txt2txt_model, txt2img_model, imgtxt2txt_model
from utils import HF, API, CUSTOM, BATCH_SIZE
from typing import Dict


# Base class for inference
class Infer(ABC):

    def __init__(self, model_name, model_type=HF):
        self.model_name = model_name
        self.model_type = model_type

    @abstractmethod
    def infer_dataset(self, dataset, batch_size=1):
        """inference on one datasets.Dataset

        Args:
            dataset (datasets.Dataset): evaluation dataset
            batch_size (int, optional): _description_. Defaults to 1.
        """
        pass


# text to text inference
class Txt2TxtInfer(Infer):

    def __init__(self, model_name: str, model_type: str = HF, **kwargs):
        super().__init__(model_name, model_type)
        self.model = txt2txt_model(
            model_name=self.model_name, model_type=self.model_type, **kwargs
        )

    def infer_dataset(self, dataset: Dataset, batch_size: int = 1, **kwargs) -> Dataset:

        def _map(batch: Dict) -> Dict:
            if self.model_type == HF:
                response_texts = self.model(batch["prompt_text"], **kwargs)
                batch["response_text"] = [
                    r[0]["generated_text"] for r in response_texts
                ]
            elif self.model_type == API:
                pass
            elif self.model_type == CUSTOM:
                pass
            return batch

        def _save(dataset: Dataset, path="../response/txt2txt"):
            os.makedirs(path, exist_ok=True)
            dataset.to_csv(
                os.path.join(
                    path,
                    self.model_name
                    + "-"
                    + self.model_type
                    + "-"
                    + "txt2txt_response.csv",
                )
            )

        response_dataset = dataset.map(_map, batched=True, batch_size=batch_size)
        _save(response_dataset)
        return response_dataset


# text to image inference
class Txt2ImgInfer(Infer):

    def __init__(self, model_name: str, model_type: str = HF, **kwargs):
        super().__init__(model_name, model_type)
        self.model = txt2img_model(
            model_name=self.model_name, model_type=self.model_type, **kwargs
        )
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

    def infer_dataset(self, dataset: Dataset, batch_size: int = 1, **kwargs) -> Dataset:

        def _save_response_images(image):
            pass

        def _map(batch: Dict) -> Dict:
            if self.model_type == HF:
                pass
            elif self.model_type == API:
                pass
            elif self.model_type == CUSTOM:
                pass

        return dataset.map(_map, batched=True, batch_size=batch_size)


# image text to text inference
class ImgTxt2TxtInfer(Infer):

    def __init__(self, model_name, model_type=HF):
        super().__init__(model_name, model_type)
        self.model = imgtxt2txt_model(
            model_name=self.model_name, model_type=self.model_type
        )

    def infer_dataset(self, dataset, batch_size=BATCH_SIZE):
        pass
