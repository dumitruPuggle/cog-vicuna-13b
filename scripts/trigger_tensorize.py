from tensorize_model import tensorize_model
from path_config import model_name, model_path, model_dtype


model = tensorize_model(dtype=model_dtype, model_name=model_name,
                        model_path=model_path, tensorizer_path=model_path)
