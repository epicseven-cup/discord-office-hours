FROM python:3.7.6
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "-u", "bot.py", "<token>"]