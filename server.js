require('dotenv').config();
const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors());

// База данных
const db = new sqlite3.Database('./database.db', (err) => {
    if (err) console.error(err);
    db.run(`CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )`);
    db.run(`CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        content TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )`);
});

// Регистрация
app.post('/register', async (req, res) => {
    const { username, password } = req.body;
    const hashedPassword = await bcrypt.hash(password, 10);
    db.run("INSERT INTO users (username, password) VALUES (?, ?)", [username, hashedPassword], function(err) {
        if (err) return res.status(400).json({ error: "Пользователь уже существует" });
        res.json({ message: "Регистрация успешна" });
    });
});

// Логин
app.post('/login', (req, res) => {
    const { username, password } = req.body;
    db.get("SELECT * FROM users WHERE username = ?", [username], async (err, user) => {
        if (!user || !(await bcrypt.compare(password, user.password))) {
            return res.status(401).json({ error: "Неверный логин или пароль" });
        }
        const token = jwt.sign({ id: user.id }, process.env.JWT_SECRET, { expiresIn: '1h' });
        res.json({ token });
    });
});

// Создание проекта
app.post('/projects', (req, res) => {
    const { userId, name, content } = req.body;
    db.run("INSERT INTO projects (user_id, name, content) VALUES (?, ?, ?)", [userId, name, content], function(err) {
        if (err) return res.status(500).json({ error: "Ошибка сохранения проекта" });
        res.json({ message: "Проект сохранён!" });
    });
});

// Получение проектов пользователя
app.get('/projects/:userId', (req, res) => {
    db.all("SELECT * FROM projects WHERE user_id = ?", [req.params.userId], (err, projects) => {
        if (err) return res.status(500).json({ error: "Ошибка загрузки проектов" });
        res.json(projects);
    });
});

// Редактирование проекта
app.put('/projects/:id', (req, res) => {
    const { content } = req.body;
    db.run("UPDATE projects SET content = ? WHERE id = ?", [content, req.params.id], function(err) {
        if (err) return res.status(500).json({ error: "Ошибка обновления проекта" });
        res.json({ message: "Проект обновлён!" });
    });
});

app.listen(3000, () => console.log('Сервер работает на http://localhost:3000'));
