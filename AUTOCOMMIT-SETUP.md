## Setting Up the `autocommit` Script

`autocommit` is a command-line tool designed to assist developers in generating meaningful commit messages based on staged changes in a Git repository. By leveraging advanced language models, the tool provides contextually relevant commit messages, streamlining the development workflow and ensuring consistent commit conventions. Before using, ensure you've set up the tool with the appropriate OpenAI API key.

### 1. **Prerequisites**:

Ensure you have Python installed on your machine. The script will first look for `python3`, and if not found, will fallback to `python`.

Install the OpenAI Python SDK. You can do this using pip:

```bash
pip install openai
```

### 2. **Installation**:

1. Download the `autocommit` script from the provided link or location.
2. Move the script to a directory in your PATH for easy access:

```bash
sudo mv /path/to/autocommit.py /usr/local/bin/autocommit
```

3. Make the script executable:

```bash
chmod +x /usr/local/bin/autocommit
```

### 3. **Configuration**:

Before using the script, set up your OpenAI API key. 

Open the script in a text editor:

```bash
nano /usr/local/bin/autocommit
```

Find the line:

```python
openai.api_key = 'YOUR_OPENAI_API_KEY'
```

Replace `YOUR_OPENAI_API_KEY` with your actual API key:

```python
openai.api_key = 'YOUR_ACTUAL_OPENAI_API_KEY'
```

Save and close the file.

### 4. **Usage**:

Before generating a commit message, ensure your changes are staged. If you're unfamiliar with staging, it's the process of marking changes for inclusion in the next commit. Use:

```bash
git add <filename>
```

Alternatively, the `autocommit` script provides a `--stage-all` flag to automatically stage all changes for you:

```bash
autocommit --stage-all
```

Once staged, run the script:

```bash
autocommit
```

The script will suggest a commit message based on the staged changes. Choose to accept the suggested message or generate a new one.

### **Note**:

Always review the auto-generated commit messages before pushing. Ensure they accurately capture the essence of your changes. If needed, amend the last commit with a manually crafted message:

```bash
git commit --amend
```
