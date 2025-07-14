FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# システムパッケージの更新とuvのインストール
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# uvをPATHに追加
ENV PATH="/root/.cargo/bin:${PATH}"

# プロジェクトファイルをコピー
COPY pyproject.toml uv.lock ./

# 依存関係のインストール
RUN uv sync --frozen

# アプリケーションコードをコピー
COPY . .

# ポート8000を公開
EXPOSE 8000

# アプリケーションの起動
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]