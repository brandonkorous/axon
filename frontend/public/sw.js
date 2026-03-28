/* Axon service worker — handles push notifications and click-to-navigate. */

self.addEventListener("push", (event) => {
  if (!event.data) return;

  let payload;
  try {
    payload = event.data.json();
  } catch {
    payload = { title: "Axon", body: event.data.text() };
  }

  const { title, body, icon, tag, data } = payload;

  event.waitUntil(
    self.registration.showNotification(title || "Axon", {
      body: body || "",
      icon: icon || "/favicon.svg",
      tag: tag || undefined,
      data: data || {},
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  const url = event.notification.data?.url || "/";

  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((windowClients) => {
      // Focus an existing Axon tab and navigate it
      for (const client of windowClients) {
        if (client.url.includes(self.location.origin)) {
          client.focus();
          client.navigate(url);
          return;
        }
      }
      // No existing tab — open a new one
      return clients.openWindow(url);
    })
  );
});
