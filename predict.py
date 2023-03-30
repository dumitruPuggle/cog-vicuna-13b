from typing import List
from collections import OrderedDict
from cog import BasePredictor, Input
from transformers import T5ForConditionalGeneration, T5Tokenizer, AutoConfig, AutoModelForSeq2SeqLM
from train import resolve_model, load_tokenizer, MODEL_NAME
import torch
from tensorizer import TensorDeserializer
from tensorizer.utils import no_init_or_tensor
# two things we need - configuration of model & configuration/actual tokenizer
# in train, we...right now load configuration of model and model from the container
# tokenizer doesn't change, just need to disambiguate model_name from tensorizer.

class Predictor(BasePredictor):
    def setup(self, weights='tuned_weights.tensorized'):
        model_name = resolve_model(weights)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        if 'tensorized' in weights: #TODO: this is not the best way to determine whether something is or is not tensorized.
            self.model = self.load_tensorizer(weights)
        else:
            self.model = T5ForConditionalGeneration.from_pretrained(
                model_name, cache_dir='pretrained_weights', torch_dtype=torch.float16, local_files_only=True
            )
            self.model.to(self.device)
        self.tokenizer = load_tokenizer()

    def load_tensorizer(self, weights):
        config = AutoConfig.from_pretrained(MODEL_NAME)

        model = no_init_or_tensor(
            lambda: AutoModelForSeq2SeqLM.from_pretrained(
                None, config=config, state_dict=OrderedDict()
            )
        )
        des = TensorDeserializer(weights, plaid_mode=True)
        des.load_into_module(model)
        self.model = model

    def predict(
        self,
        prompt: str = Input(description=f"Prompt to send to FLAN-T5."),
        n: int = Input(
            description="Number of output sequences to generate", default=1, ge=1, le=5
        ),
        max_length: int = Input(
            description="Maximum number of tokens to generate. A word is generally 2-3 tokens",
            ge=1,
            default=50,
        ),
        temperature: float = Input(
            description="Adjusts randomness of outputs, greater than 1 is random and 0 is deterministic, 0.75 is a good starting value.",
            ge=0.01,
            le=5,
            default=0.75,
        ),
        top_p: float = Input(
            description="When decoding text, samples from the top p percentage of most likely tokens; lower to ignore less likely tokens",
            ge=0.01,
            le=1.0,
            default=1.0,
        ),
        repetition_penalty: float = Input(
            description="Penalty for repeated words in generated text; 1 is no penalty, values greater than 1 discourage repetition, less than 1 encourage it.",
            ge=0.01,
            le=5,
            default=1,
        ),
        debug : bool = Input(
            description="provide debugging output in logs",
            default=False
        )
    ) -> List[str]:
        input = self.tokenizer(prompt, return_tensors="pt").input_ids.to(self.device)

        outputs = self.model.generate(
            input,
            num_return_sequences=n,
            max_length=max_length,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
        )
        if debug:
            print(f"cur memory: {torch.cuda.memory_allocated()}")
            print(f"max allocated: {torch.cuda.max_memory_allocated()}")
            print(f"peak memory: {torch.cuda.max_memory_reserved()}")
        out = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
        return out


class EightBitPredictor(Predictor):
    """subclass s.t. we can configure whether a model is loaded in 8bit mode from cog.yaml"""

    def setup(self, weights=None):
        model_name = resolve_model(weights)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = T5ForConditionalGeneration.from_pretrained(
            model_name, local_files_only=True, load_in_8bit=True, device_map="auto"
        )
        self.tokenizer = T5Tokenizer.from_pretrained(model_name, local_files_only=True)
