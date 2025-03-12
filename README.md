# Project Noteflow

## [frontend](https://github.com/cse115a-noteflow/noteflow) - backend

## About

NoteFlow is a collaborative, AI-assisted note-taking application that helps students write better notes. With NoteFlow, you can:

- Write your notes in an intuitive WYSIWYG editor
- Ask questions about your note using a RAG search algorithm
- Summarize your notes and generate study materials
- Collaborate with peers in real time

## How It's Made

Front-end: React/TypeScript/CSS
Back end: Flask/Python

## Installation

For ease of development and deployment, NoteFlow is split into two responsitories: the frontend and the backend. To develop, you must clone both repositories and follow the setup guide below.

### Frontend Setup

1. Navigate to directory

```
cd noteflow
```

2. Install dependencies

```
npm install
```

3. Start the development server

```
npm run dev
```

### Backend Setup

1. Navigate to directory

```
cd noteflow-server
```

2.  Create a .env file in the directory such that

```
OPENAI_API_KEY='INSERT YOUR OPENAI API KEY HERE'
PINECONE_API_KEY='INSERT YOUR PINECONE API KEY HERE'
```

You can get and obtain your OpenAI API key [here](https://platform.openai.com/api-keys) and your Pinecone API key [here](https://docs.pinecone.io/guides/projects/manage-api-keys). 2. Run the backend server

```
python ./main.py
```
