# SmartQueue – Smart Queue Management System

A web-based queue management system built with Python Flask that allows customers to digitally join a queue, receive a queue token, track their position, and monitor their service status. Administrators can manage the queue through a dedicated dashboard.

---

## 📌 Project Overview

Traditional queue systems require customers to physically stand in line and wait for their turn. This can lead to long waiting times, overcrowding, and inconvenience.

**SmartQueue** provides a digital alternative. Customers can join the queue using a web interface and receive a unique token without physically standing in line. Administrators can monitor the queue and call customers in an organized manner.

The system also provides a public display for showing the currently serving token.

---

## 🎯 Problem Statement

Traditional queue management systems have several limitations:

- Customers need to physically wait in line.
- There is no convenient way to track queue position.
- Customers may not know when their turn is approaching.
- Manual queue management can be inefficient.
- Physical queues can result in overcrowding.

SmartQueue addresses these problems by providing a simple digital queue management solution.

---

## 🎯 Objectives

The main objectives of SmartQueue are:

1. To provide a digital queue registration system.
2. To automatically generate unique queue tokens.
3. To allow customers to track their queue status.
4. To allow customers to cancel their queue entry.
5. To provide administrators with a queue management dashboard.
6. To allow administrators to call the next customer.
7. To provide a public display for the currently serving token.
8. To store queue information using a database.
9. To provide a simple and user-friendly interface.

---

## ✨ Features

### 👤 Customer Features

- Join the queue using their name.
- Receive an automatically generated token.
- View their queue position.
- Monitor their current queue status.
- Refresh the status page without creating duplicate queue entries.
- Cancel their queue entry when required.

### 🔐 Administrator Features

- Secure admin login.
- View current queue information.
- View queue statistics.
- Monitor waiting customers.
- Call the next customer.
- Manage customer queue status.
- Access the administration dashboard.

### 📺 Public Display

- Displays the currently serving token.
- Shows the customer currently being served.
- Provides a simple interface suitable for a reception or waiting area display.

---

## 🧩 System Modules

The application is divided into the following major modules:

### 1. Customer Module

Responsible for:

- Customer registration.
- Token generation.
- Queue position tracking.
- Status monitoring.
- Queue cancellation.

### 2. Admin Module

Responsible for:

- Administrator authentication.
- Queue monitoring.
- Calling the next customer.
- Managing queue operations.

### 3. Public Display Module

Responsible for displaying:

- Current serving token.
- Current customer information.
- Queue status.

### 4. Database Module

Responsible for storing:

- Customer information.
- Queue tokens.
- Queue status.
- Queue-related information.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|------------|---------|
| Python | Backend programming |
| Flask | Web application framework |
| HTML | Page structure |
| CSS | User interface and styling |
| SQLite | Database |
| Jinja2 | Dynamic HTML templates |
| Git | Version control |
| GitHub | Source code repository |

---

## 📁 Project Structure

The project follows a structure similar to:

```text
SmartQueue/
│
├── app.py
│
├── database/
│   └── ...
│
├── static/
│   └── style.css
│
├── templates/
│   ├── index.html
│   ├── status.html
│   ├── admin.html
│   ├── display.html
│   └── ...
│
├── README.md
│
└── ...