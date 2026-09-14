# Browser QA scope

Executed Chromium rendering and interaction checks are in browser_report.json. The generated HTML was loaded via Playwright set_content because this runtime blocks file:// navigation. No policy was changed; only the newly generated HTML text was rendered in memory.

Checks: Markdown rendering, scope notice, 29 document navigation entries, 16 source cards, source commit popup, a Chinese agent prompt retrieving C032, keyword filtering, mobile menu, horizontal overflow, JavaScript errors and external HTTP requests.

This does not test browser clipboard permissions across every desktop platform, all possible search questions, or real LLM integration. A file:// deployment was not directly exercised in this runtime.
