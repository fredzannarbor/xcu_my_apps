import os

from aleph_alpha_client import Document, AlephAlphaClient, AlephAlphaModel, SummarizationRequest


def docx2textsummary(docx_file):
    model = AlephAlphaModel(
        AlephAlphaClient(host="https://api.aleph-alpha.com", token=os.getenv("ALEPH_ALPHA_API_TOKEN")),
        # You need to choose a model with qa support for this example.
        model_name="luminous-extended"
    )

    document = Document.from_docx_file(docx_file)

    request = SummarizationRequest(document)

    result = model.summarize(request)

    print(result.summary)

    return result.summary


def text2textsummary(text):
    model = AlephAlphaModel(
        AlephAlphaClient(host="https://api.aleph-alpha.com", token=os.getenv("AA_TOKEN")),
        # You need to choose a model with qa support for this example.
        model_name="luminous-extended"
    )

    document = Document.from_text(text)

    request = SummarizationRequest(document)

    result = model.summarize(request)

    print(result.summary)

    return result.summary


def tokenize(text):
    from aleph_alpha_client import AlephAlphaClient, AlephAlphaModel, TokenizationRequest
    import os

    model = AlephAlphaModel(
        AlephAlphaClient(host="https://api.aleph-alpha.com", token=os.getenv("AA_TOKEN")),
        model_name="luminous-extended"
    )

    # You need to choose a model with qa support and multimodal capabilities for this example.
    request = TokenizationRequest(prompt="This is an example.", tokens=True, token_ids=True)
    response = model.tokenize(request)

    print(response)
    return response


if __name__ == "__main__":
    result = docx2textsummary("test/docx/lorem.docx")
    print(result)
