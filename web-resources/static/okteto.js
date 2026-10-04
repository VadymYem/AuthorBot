/*
 * SPDX-FileCopyrightText: 2026 Vadym Yemelianov (AuthorChe / VadymYem), AuthorBot integration and maintenance
 * SPDX-License-Identifier: AGPL-3.0-only
 * Existing upstream copyright and license notices are retained; see NOTICE.md and LICENSE.
 */

function okteto() {
    fetch("/okteto", {
            method: "POST",
            credentials: "include",
            body: window.location.href
        })
        .then(response => response.text())
        .then((response) => {
            if (response == "WAIT") {
                setTimeout(() => {
                    okteto();
                }, 5000);
            }
        })
}

okteto()