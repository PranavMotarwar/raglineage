"""Query a text-based PDF: python examples/basic_usage/pdf_example.py handbook.pdf.

Install first: pip install 'raglineage[pdf]'
Page citations use physical PDF pages starting at 1, not printed page labels.
"""

import argparse

from raglineage import RagLineage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Text-based PDF path or directory containing PDFs")
    parser.add_argument("--question", default="What is the refund policy?")
    args = parser.parse_args()

    rag = RagLineage(source=args.source, embed_backend="hash", store_backend="numpy")
    rag.build(version="v1")
    answer = rag.query(args.question, k=3)
    print(answer.to_markdown())
    for entry in answer.lineage:
        if entry.source.type == "pdf":
            print(f"Citation: {entry.source.uri}, page {entry.source.page}")
    hits = rag.retrieve(args.question, k=3)
    print("\nContext for your preferred LLM:")
    print(rag.format_context_for_llm(hits))
    print("\nAudit:")
    print(rag.audit(answer).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
