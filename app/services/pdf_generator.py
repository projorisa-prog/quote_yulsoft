The user wants me to apply the suggested edit to the original code. The suggested edit is a complete replacement of the original code - it's a different implementation with async functions, different imports, and different structure.

Let me analyze the differences:
1. Original uses a class `PDFGenerator` with methods
2. Suggested edit uses standalone async functions
3. Different imports (no uuid, datetime, Optional, etc.)
4. Different template handling (uses "base.html" instead of design-specific templates)
5. Different path resolution (uses __file__ based paths)
6. Uses `Quote` model instead of `QuoteResponse` schema
7. Uses `quote.design_key.value` (enum) instead of string

The user said "Apply the SUGGESTED EDIT to the ORIGINAL CODE" and "Output the complete modified file". Since the suggested edit is a complete rewrite, I should output the suggested edit as the complete file.

But wait - the user also said "Preserve all unchanged code exactly as-is" and "Leave existing comments in place unless changes require modifying them". However, the suggested edit is a complete replacement with different structure. There's no "unchanged code" to preserve since it's a totally different implementation.

I think the intent is to replace the entire file with the suggested edit. Let me output the suggested edit as the complete modified```
import os
from pathlib import Path
from typing import BinaryIO
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

from app.models.quote import Quote


font_config = FontConfiguration()


async def generate_pdf(quote: Quote) -> bytes:
    """WeasyPrint를 사용하여 견적서 PDF 생성"""

    # 템플릿 경로
    template_dir = Path(__file__).parent.parent / "templates" / "quote"

    # 디자인별 CSS 선택
    design_css_map = {
        "classic": "design-classic.css",
        "modern": "design-modern.css",
        "color": "design-color.css",
    }
    design_css = design_css_map.get(quote.design_key.value, "design-modern.css")

    # HTML 렌더링
    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("base.html")

    html_content = template.render(
            quote=quote,
        design_key=quote.design_key.value,
        watermark_text=quote.watermark_text,
        )
        
    # CSS 파일들 로드
    base_css_path = template_dir.parent / "static" / "css" / "quote-base.css"
    design_css_path = template_dir.parent / "static" / "css" / design_css
        stylesheets = []
    if base_css_path.exists():
        stylesheets.append(CSS(filename=str(base_css_path), font_config=font_config))
    if design_css_path.exists():
        stylesheets.append(CSS(filename=str(design_css_path), font_config=font_config))
        
    # 워터마크 CSS 동적 추가
        if quote.watermark_text:
            watermark_css = CSS(string=f"""
                @page {{
                    @bottom-center {{
                        content: "{quote.watermark_text}";
                        font-size: 8pt;
                    color: #999;
                        font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
                    }}
                }}
        """, font_config=font_config)
            stylesheets.append(watermark_css)
        
    # PDF 생성
    html_doc = HTML(string=html_content, base_url=str(template_dir))
    pdf_bytes = html_doc.write_pdf(stylesheets=stylesheets, font_config=font_config)
        
        return pdf_bytes


async def generate_pdf_to_file(quote: Quote, output_path: str) -> None:
    """PDF를 파일로 저장"""
    pdf_bytes = await generate_pdf(quote)
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)
