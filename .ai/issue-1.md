# WordCount Pro: поддержка слов/строк/символов + CLI + edge-cases

•	Добавить модуль src/wordcount.py с функциями:
•	count_words(text: str) -> int — количество слов (слово = последовательность непробельных символов). Множественные пробелы, табы и переносы строк не считаются словами.
•	count_lines(text: str) -> int — количество строк. Пустая строка "" → 0. Если текст не пустой и не заканчивается \n, это тоже строка.
•	count_chars(text: str) -> int — количество символов как есть, включая пробелы и \n.
•	Добавить CLI python -m src.wordcount:
•	если передан аргумент --text "..." → считать по этой строке
•	если передан --file path → считать по файлу (utf-8)
•	вывод строго в формате:
words=
lines=
chars=
• Тесты: tests/test_wordcount.py (pytest) минимум 6 тестов:
• "" → words=0 lines=0 chars=0
• " hello world " → words=2 lines=1 chars=17 (важно: пробелы считаются в chars)
• "line1\nline2\n" → words=2 lines=2 chars=12
• "one\n" → words=1 lines=1 chars=4
• "one" → words=1 lines=1 chars=3
• "\n\n" → words=0 lines=2 chars=2
• Добавить init.py только если реально нужно для импортов/запуска.
• CI не должен падать из-за black: код должен соответствовать black.

Generated: 2026-01-30 20:04:53.850683