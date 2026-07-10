# Frontend dev image. Owner: Person D. Vite dev server; for prod, add a build+nginx stage.
FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
