#!/usr/bin/env python3
import sys
sys.path.insert(0, 'C:\\VSH-VSH\\VSH_Project_MVP')

from vsh_api.main import app
import uvicorn

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=3002, reload=True)
