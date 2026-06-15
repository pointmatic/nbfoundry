# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
import marimo

app = marimo.App()


@app.cell
def _(data):
    total = sum(data)
    return (total,)


if __name__ == "__main__":
    app.run()
