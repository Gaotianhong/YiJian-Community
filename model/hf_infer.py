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
from matplotlib.pyplot import cla
import torch
from .base_infer import Infer
from data import save_image
from transformers import pipeline
from datetime import datetime
from datasets import Dataset
from diffusers import DiffusionPipeline
from PIL import Image
from utils import (
    BATCH_SIZE,
    DEVICE_MAP,
    MAX_NEW_TOKENS,
    RETURN_FULL_TEXT,
    DO_SAMPLE,
    USE_SAFETENSORS,
    SEED,
    TORCH_DTYPE,
    TEMPERATURE,
)


class HFTxt2TxtInfer(Infer):

    def __init__(self, model_name: str, device_map: str = DEVICE_MAP, **kwargs):
        super().__init__(model_name)
        try:
            self.infer = pipeline(
                "text-generation", model=model_name, device_map=device_map, **kwargs
            )
        except Exception as e:
            print(e)
            print("reloading model ...")
            self.infer = pipeline("text-generation", model=model_name, **kwargs)

    def infer_data(
        self,
        data: str,
        max_new_tokens: int = MAX_NEW_TOKENS,
        do_sample: bool = DO_SAMPLE,
        temperature: float = TEMPERATURE,
        **kwargs,
    ) -> str:
        return self.infer(
            data,
            max_new_tokens=max_new_tokens,
            return_full_text=RETURN_FULL_TEXT,
            do_sample=do_sample,
            temperature=temperature,
            **kwargs,
        )[0]["generated_text"]

    def infer_dataset(
        self,
        dataset: Dataset,
        target_column: str = "prompt_text",
        batch_size: int = BATCH_SIZE,
        max_new_tokens: int = MAX_NEW_TOKENS,
        do_sample: bool = DO_SAMPLE,
        temperature: float = TEMPERATURE,
        **kwargs,
    ) -> Dataset:
        if not self.infer.tokenizer.pad_token:
            self.infer.tokenizer.pad_token_id = self.infer.model.config.eos_token_id
        if not self.infer.model.config.is_encoder_decoder:
            self.infer.tokenizer.padding_side = "left"

        res = self.infer(
            dataset[target_column],
            batch_size=batch_size,
            max_new_tokens=max_new_tokens,
            return_full_text=RETURN_FULL_TEXT,
            do_sample=do_sample,
            temperature=temperature,
            **kwargs,
        )

        response_texts = [r[0]["generated_text"] for r in res]

        return dataset.add_column("response_text", response_texts)


class vLLMTxt2TxtInfer(Infer):

    def __init__(self, model_name):
        super().__init__(model_name)

    def infer_data(self, data: str):
        return super().infer_data(data)

    def infer_dataset(self, dataset: Dataset) -> Dataset:
        return super().infer_dataset(dataset)


class HFTxt2ImgInfer(Infer):

    def __init__(
        self,
        model_name: str,
        device_map: str = DEVICE_MAP,
        use_safetensors=USE_SAFETENSORS,
        torch_dtype=TORCH_DTYPE,
        **kwargs,
    ):
        super().__init__(model_name)
        try:
            self.infer = DiffusionPipeline.from_pretrained(
                model_name,
                device_map=device_map,
                use_safetensors=use_safetensors,
                torch_dtype=torch_dtype,
                **kwargs,
            )
        except Exception as e:
            print(e)
            print("reloading model ...")
            self.infer = DiffusionPipeline.from_pretrained(
                model_name,
                use_safetensors=use_safetensors,
                torch_dtype=torch_dtype,
                **kwargs,
            )
        if torch.cuda.is_available():
            self.generator = torch.Generator("cuda").manual_seed(SEED)
        else:
            self.generator = torch.Generator().manual_seed(SEED)
        self.infer.enable_xformers_memory_efficient_attention()
        self.infer.enable_model_cpu_offload()

    def infer_data(
        self,
        data: str,
        **kwargs,
    ) -> Image.Image:
        return self.infer(data, generator=self.generator, **kwargs).images[0]

    def infer_dataset(
        self,
        dataset: Dataset,
        batch_size: int = BATCH_SIZE,
        **kwargs,
    ) -> Dataset:
        image_save_path = os.path.join(
            os.getcwd(), "images_txt2img_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        os.makedirs(image_save_path, exist_ok=True)

        response_images = []
        for data in dataset.iter(batch_size=batch_size):
            images = self.infer(data["prompt_text"], generator=self.generator, **kwargs).images
            response_images.extend(
                save_image(image_save_path, self.model_name, data["prompt_text"], images)
            )
        return dataset.add_column("response_image", response_images)
