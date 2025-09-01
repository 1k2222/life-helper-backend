from transformers import pipeline, AutoTokenizer, AutoModelForVision2Seq


def extract_pdf():
    tokenizer = AutoTokenizer.from_pretrained("ByteDance/Dolphin")
    model = AutoModelForVision2Seq.from_pretrained("ByteDance/Dolphin")
    print(type(tokenizer))
    print(type(model))


if __name__ == '__main__':
    extract_pdf()
