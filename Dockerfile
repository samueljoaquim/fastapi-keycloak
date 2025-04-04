FROM python:3.13
RUN mkdir /app
WORKDIR /app
RUN pip install pipenv
ADD Pipfile Pipfile
ADD Pipfile.lock Pipfile.lock
RUN pipenv install
ADD *.py .
ADD routers ./routers
ADD services ./services
ADD static ./static
ADD utils ./utils
CMD ["pipenv", "run", "fastapi", "run", "./main.py"]
