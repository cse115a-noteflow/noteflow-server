# Project NoteFlow

## About

NoteFlow is a collaborative, AI-assisted note-taking application that helps students write better notes. 

Specific AI tasks that our application is able to do are querying for structured answers from note documents, summarizing notes, and generating study material from notes.

## How It's Made

Tech Used: TypeScript, CSS, Python

## Installation

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
You can get and obtain your OpenAI API key [here](https://platform.openai.com/api-keys) and your Pinecone API key [here](https://docs.pinecone.io/guides/projects/manage-api-keys).
2. Run the backend server
```
python ./main.py
```