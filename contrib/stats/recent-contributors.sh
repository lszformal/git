#!/bin/sh

set -eu

usage() {
  cat <<USAGE >&2
usage: ${0##*/} [--since <date>] [--limit <count>] [-C <repo>]

List the most active contributors in a repository since a given date.

Options:
  --since <date>   Limit commits to those after the given date (default: "30 days ago").
  --limit <count>  Maximum number of contributors to display (default: 20).
  -C <repo>        Run as if git was started in <repo> (default: current directory).
  -h, --help       Show this help message.
USAGE
  exit 1
}

since="30 days ago"
limit=20
repo="."

while [ $# -gt 0 ]; do
  case "$1" in
  --since)
    [ $# -ge 2 ] || usage
    since="$2"
    shift 2
    ;;
  --limit)
    [ $# -ge 2 ] || usage
    limit="$2"
    shift 2
    ;;
  -C)
    [ $# -ge 2 ] || usage
    repo="$2"
    shift 2
    ;;
  -h|--help)
    usage
    ;;
  *)
    usage
    ;;
  esac
done

if ! expr "$limit" : '^[0-9][0-9]*$' >/dev/null; then
  echo "error: --limit must be a non-negative integer" >&2
  exit 1
fi

contributors=$(git -C "$repo" log --since="$since" --format='%an <%ae>' \
  | sed 's/^ *//;s/ *$//' \
  | sed '/^$/d' \
  | sort \
  | uniq -c \
  | sort -nr \
  | head -n "$limit")

if [ -z "$contributors" ]; then
  echo "No contributors found since $since."
  exit 0
fi

echo "Top contributors since $since (limit $limit):"
echo "$contributors"
