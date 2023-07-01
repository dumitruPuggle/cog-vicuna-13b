import os

model_name = "TheBloke/Wizard-Vicuna-7B-Uncensored-HF"
model_path = os.path.join(os.getcwd(), "model")
tensorized_path = os.path.join(
    os.getcwd(), "model", "vicuna-7B-Uncensored-HF.tensors")
tokenizer_path = os.path.join(
    os.getcwd(), "model")
model_dtype = "fp16"
