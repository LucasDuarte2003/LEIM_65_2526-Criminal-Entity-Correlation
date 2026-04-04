import torch
from torch.utils.data import Dataset
from transformers import AutoTokenizer, XLMRobertaForTokenClassification


class NERDataset(Dataset):
    def __init__(self, raw_data, tokenizer, label2id, max_length=128):
        self.examples = []

        for sentence in raw_data:
            words = [pair[0] for pair in sentence]
            labels = [pair[1] for pair in sentence]

            encoding = tokenizer(
                words,
                is_split_into_words=True,
                truncation=True,
                max_length=max_length,
                padding="max_length",
                return_tensors="pt"
            )

            word_ids = encoding.word_ids(batch_index=0)
            aligned_labels = []
            previous_word_id = None

            for word_id in word_ids:
                if word_id is None:
                    aligned_labels.append(-100)
                elif word_id != previous_word_id:
                    aligned_labels.append(label2id[labels[word_id]])
                else:
                    aligned_labels.append(-100)
                previous_word_id = word_id

            self.examples.append({
                "input_ids": encoding["input_ids"].squeeze(),
                "attention_mask": encoding["attention_mask"].squeeze(),
                "labels": torch.tensor(aligned_labels)
            })

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return self.examples[idx]


def load_model(num_labels, label2id, id2label, model_path=None):
    MODEL_NAME = "xlm-roberta-base"  # ← multilingual, suporta português

    if model_path:
        print(f"A carregar modelo guardado de: {model_path}")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = XLMRobertaForTokenClassification.from_pretrained(model_path)
    else:
        print(f"A descarregar {MODEL_NAME} da HuggingFace (~1GB, só na primeira vez)...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = XLMRobertaForTokenClassification.from_pretrained(
            MODEL_NAME,
            num_labels=num_labels,
            id2label=id2label,
            label2id=label2id,
            ignore_mismatched_sizes=True
        )

    return model, tokenizer