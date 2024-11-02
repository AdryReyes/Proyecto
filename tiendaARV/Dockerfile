FROM python:3.12.7-alpine3.20

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN apk update \
    && apk add --no-cache gcc musl-dev postgresql-dev python3-dev libffi-dev \
    && pip install --upgrade pip

COPY ./requirements.txt ./

RUN pip install -r requirements.txt

COPY ./ ./

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

#docker run --name proyectoTienda -p 5432:5432 -e POSTGRES_PASSWORD=usuario -d postgres

#docker-compose exec postgres psql -U usuario -d proyectoTienda
#docker exec -it proyectoTienda /bin/bash
