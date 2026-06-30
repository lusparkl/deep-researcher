# 📚 Deep Researcher

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.14-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-d94e0b?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

*Assistant to find what you're up to easily*


</div>

---

## ✨ Overview

Deep Researcher is my personal project that I've built to learn langgraph technology and how AI agents are actually built.

[Telegram Bot](https://t.me/lusp_research_bot)

###  Key Highlights
-  **Agentic research flow* - There is multiple data analysts that dive deep into the topic to make best report for the user.
-  **Grounded responses** - All responses are grounded on data from web search and wikipedia.
-  **Cited reports** - All reports have sources and all data is cited. 
-  **Topic clarification** - User topic is first checked by agent to make sure that it's clear, if not it'll ask user for the clarifications.
-  **Telegram wrapper** - It's acessible as a telegram bot, so anyone can easily test it.
-  **Provider handling** - I used Hack Club AI api by default, but if it reached limit or have some errors we fallback to OpenAI API.
-  **Daily limits** - Telegram bot has a daily limit of 1 research/day because tokens aren't infinitive.

---

##  Graph Structure

![Graph structure](/app/assets/main_graph.png)

---

### AI Usage

Mostly I made this project by myself, but I used AI to write better prompts for another AI's :>
And also I did a little bit of debugging of AI and wikipedia api's using codex.
---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

### Made with ❤️ 

[⬆ Back to top](#-deep-researcher)

</div>

