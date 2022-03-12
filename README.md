Migrate all repositories from one gitea instance to another.

For my use case, I captured the python environment in a Docker container. It can be build and
started using the `run.sh` script. In the container, I did something like the following:

```
python3 migrator.py --src-token natu-token.txt --dst-token monferno-token.txt --src-host https://git.zackmarvel.com --dst-host git-beta.zackmarvel.com
```


Notes:

- Discovered misconfiguration in source instance (natu). `server.ROOT_URL` was `http://natu.zackmarvel.com:3000` (only accessible from localhost). This manifested as timeouts from the destination server (monferno).
- Maybe I have an nginx configuration issue on my server--some URLs didn't seem to get redirected to the HTTPS url. I had to update my URLs to use https.
- Importantly, I had to provide the `'service': 'gitea'` parameters in the request to support issue migration, etc.
- I had mirrored some other projects to my instance. I ended up only using the migration for my user--it would maybe have to be a little smarter to handle organizations.
- The last snafu I ran into was mysterious failures during migration. If I unchecked the issues, wiki, etc., it worked. It turned out I was running 1.16.2 in the source instance and 1.16.0 in the destination. I updated the latter and my script worked.
