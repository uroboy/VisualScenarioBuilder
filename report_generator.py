"""
Visual Scenario Builder - テスト結果レポート生成

results/ 配下の *_result.json（TestResultManager が保存するもの）を集計し、
外部ライブラリ不要の単一HTMLファイルとしてレポートを出力する。
"""

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from test_utils import TestResultManager

STYLE = """
:root {
  color-scheme: light dark;
  --bg: #f7f8fa;
  --surface: #ffffff;
  --text: #1a1d23;
  --text-muted: #5b6270;
  --border: #e2e5ea;
  --pass: #1e8e5a;
  --pass-bg: #e6f6ee;
  --fail: #c0392b;
  --fail-bg: #fbeae8;
  --accent: #3457d5;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #14161a;
    --surface: #1d2026;
    --text: #e8eaed;
    --text-muted: #9aa0ab;
    --border: #2c303a;
    --pass: #4fd68f;
    --pass-bg: #163727;
    --fail: #ff8478;
    --fail-bg: #3a1f1c;
    --accent: #7c93ff;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 2rem 1.5rem 4rem;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
}
.wrap { max-width: 960px; margin: 0 auto; }
h1 { font-size: 1.5rem; margin: 0 0 0.25rem; }
.generated-at { color: var(--text-muted); font-size: 0.85rem; margin: 0 0 1.75rem; }
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.75rem;
}
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.9rem 1rem;
}
.card .label { font-size: 0.78rem; color: var(--text-muted); margin-bottom: 0.35rem; }
.card .value { font-size: 1.5rem; font-weight: 600; }
.card .value.pass { color: var(--pass); }
.card .value.fail { color: var(--fail); }
.bar {
  height: 10px;
  border-radius: 999px;
  background: var(--fail-bg);
  overflow: hidden;
  margin-bottom: 1.75rem;
  border: 1px solid var(--border);
}
.bar-fill { height: 100%; background: var(--pass); }
.filters { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.filters button {
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  border-radius: 999px;
  padding: 0.35rem 0.9rem;
  font-size: 0.82rem;
  cursor: pointer;
}
.filters button.active { border-color: var(--accent); color: var(--accent); font-weight: 600; }
.results { display: flex; flex-direction: column; gap: 0.6rem; }
.result {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 4px solid var(--pass);
  border-radius: 10px;
  padding: 0.75rem 1rem;
}
.result.failed { border-left-color: var(--fail); }
.result summary {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  list-style: none;
}
.result summary::-webkit-details-marker { display: none; }
.status-pill {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  background: var(--pass-bg);
  color: var(--pass);
  white-space: nowrap;
}
.result.failed .status-pill { background: var(--fail-bg); color: var(--fail); }
.result .name { font-weight: 600; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.result .meta { color: var(--text-muted); font-size: 0.8rem; white-space: nowrap; }
.detail { margin-top: 0.7rem; padding-top: 0.7rem; border-top: 1px solid var(--border); font-size: 0.85rem; }
.detail dl { display: grid; grid-template-columns: max-content 1fr; gap: 0.3rem 0.8rem; margin: 0; }
.detail dt { color: var(--text-muted); }
.detail dd { margin: 0; word-break: break-word; }
.error-box {
  margin-top: 0.6rem;
  background: var(--fail-bg);
  color: var(--fail);
  border-radius: 8px;
  padding: 0.6rem 0.8rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.78rem;
  white-space: pre-wrap;
}
.empty { color: var(--text-muted); text-align: center; padding: 3rem 0; }
"""

SCRIPT = """
document.querySelectorAll('.filters button').forEach(function (btn) {
  btn.addEventListener('click', function () {
    document.querySelectorAll('.filters button').forEach(function (b) { b.classList.remove('active'); });
    btn.classList.add('active');
    var filter = btn.dataset.filter;
    document.querySelectorAll('.result').forEach(function (r) {
      var show = filter === 'all' || r.dataset.status === filter;
      r.style.display = show ? '' : 'none';
    });
  });
});
"""


class HTMLReportGenerator:
    """テスト結果サマリーからスタンドアロンHTMLレポートを生成する"""

    def __init__(self, results_dir: str = "./results"):
        self.results_dir = Path(results_dir)
        self.result_manager = TestResultManager(str(self.results_dir))

    def generate(self, output_path: str = "./results/report.html") -> Path:
        summary = self.result_manager.generate_summary_report()
        html_content = self._render(summary)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(html_content, encoding="utf-8")
        return output_file

    def render_html(self) -> str:
        """既存ファイルに書き出さず、HTML文字列だけが必要な場合（API配信など）に使う"""
        return self._render(self.result_manager.generate_summary_report())

    def _render(self, summary: Dict[str, Any]) -> str:
        total = summary["total"]
        passed = summary["passed"]
        failed = summary["failed"]
        pass_rate = summary["pass_rate"]
        avg_time = summary["average_execution_time"]

        cards = f"""
        <div class="cards">
          <div class="card"><div class="label">合計実行数</div><div class="value">{total}</div></div>
          <div class="card"><div class="label">成功</div><div class="value pass">{passed}</div></div>
          <div class="card"><div class="label">失敗</div><div class="value fail">{failed}</div></div>
          <div class="card"><div class="label">成功率</div><div class="value">{pass_rate:.1f}%</div></div>
          <div class="card"><div class="label">平均実行時間</div><div class="value">{avg_time:.1f}s</div></div>
        </div>
        <div class="bar"><div class="bar-fill" style="width:{pass_rate:.1f}%"></div></div>
        """

        if total == 0:
            body = cards + '<p class="empty">テスト結果がまだありません。テストを実行すると results/ 配下にJSONが記録され、ここに表示されます。</p>'
        else:
            filters = """
            <div class="filters">
              <button data-filter="all" class="active">すべて</button>
              <button data-filter="passed">成功のみ</button>
              <button data-filter="failed">失敗のみ</button>
            </div>
            """
            rows = "\n".join(self._render_result(r) for r in summary["results"])
            body = cards + filters + f'<div class="results">{rows}</div>'

        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Visual Scenario Builder - Test Report</title>
<style>{STYLE}</style>
</head>
<body>
<div class="wrap">
  <h1>Visual Scenario Builder - Test Report</h1>
  <p class="generated-at">生成日時: {generated_at}</p>
  {body}
</div>
<script>{SCRIPT}</script>
</body>
</html>"""

    @staticmethod
    def _render_result(result: Dict[str, Any]) -> str:
        passed = result.get("passed", False)
        status_class = "" if passed else "failed"
        status_label = "PASSED" if passed else "FAILED"
        status_key = "passed" if passed else "failed"

        name = html.escape(str(result.get("scenario_name", "unknown")))
        session_id = html.escape(str(result.get("session_id", "")))
        timestamp = html.escape(str(result.get("timestamp", "")))
        exec_time = result.get("execution_time", 0) or 0

        context = result.get("context") or {}
        captured = context.get("captured_values") or {}
        current_app = context.get("current_app")

        detail_rows = f"<dt>セッションID</dt><dd>{session_id}</dd>"
        detail_rows += f"<dt>タイムスタンプ</dt><dd>{timestamp}</dd>"
        if current_app:
            detail_rows += f"<dt>実行中アプリ</dt><dd>{html.escape(str(current_app))}</dd>"
        if captured:
            captured_str = ", ".join(
                f"{html.escape(str(k))}={html.escape(str(v))}" for k, v in captured.items()
            )
            detail_rows += f"<dt>キャプチャ値</dt><dd>{captured_str}</dd>"

        error = result.get("error")
        error_html = f'<div class="error-box">{html.escape(str(error))}</div>' if error else ""

        return f"""
        <details class="result {status_class}" data-status="{status_key}">
          <summary>
            <span class="status-pill">{status_label}</span>
            <span class="name">{name}</span>
            <span class="meta">{exec_time:.1f}s</span>
          </summary>
          <div class="detail">
            <dl>{detail_rows}</dl>
            {error_html}
          </div>
        </details>
        """


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate an HTML test report from Visual Scenario Builder results")
    parser.add_argument("--results-dir", default="./results", help="結果JSONが格納されているディレクトリ")
    parser.add_argument("--output", default="./results/report.html", help="出力するHTMLファイルのパス")
    args = parser.parse_args()

    generator = HTMLReportGenerator(args.results_dir)
    output_path = generator.generate(args.output)
    print(f"Report generated: {output_path}")


if __name__ == "__main__":
    main()
