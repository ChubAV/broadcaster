FROM node:20-slim

RUN apt-get update && apt-get install -y git --no-install-recommends && rm -rf /var/lib/apt/lists/* \
    && printf '[url "https://github.com/"]\n\tinsteadOf = ssh://git@github.com/\n\tinsteadOf = git@github.com:\n' > /etc/gitconfig

WORKDIR /app

COPY package.json ./
RUN cat /etc/gitconfig && git config --list && npm install --omit=dev

COPY . .

EXPOSE 3000

CMD ["node", "index.js"]
