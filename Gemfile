# ──────────────────────────────────────────────────────────────────────────────
#  UM_Terra Sentinel — Gemfile
#  © 2026 Utsav Mukherjee · utsav.mukherjee@ibm.com · utsavmukherjee143@gmail.com
#  All rights reserved.
#
#  Pins the exact gem set that GitHub Pages uses so local and CI builds match.
#  Run locally:
#    gem install bundler
#    bundle install
#    bundle exec jekyll serve
# ──────────────────────────────────────────────────────────────────────────────

source "https://rubygems.org"

# github-pages bundles the Jekyll version, plugins and dependencies that
# GitHub Pages uses in production. Pin to the latest supported version.
gem "github-pages", group: :jekyll_plugins

# Explicitly list the plugins we declared in _config.yml so Bundler can
# resolve them even when running locally without the full github-pages meta-gem.
group :jekyll_plugins do
  gem "jekyll-seo-tag"
  gem "jekyll-sitemap"
  gem "jekyll-feed"
end

# Windows / JRuby platform guards (safe to include on all platforms)
platforms :mingw, :x64_mingw, :mswin, :jruby do
  gem "tzinfo", ">= 1", "< 3"
  gem "tzinfo-data"
end

# Performance booster for watching file changes on Windows
gem "wdm", "~> 0.1", platforms: [:mingw, :x64_mingw, :mswin]

# Locks the bundler version used in CI
gem "bundler", ">= 2.3"
