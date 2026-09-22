import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "../../drizzle/schema";

function createDb() {
  const connectionString = process.env["DATABASE_URL"];
  if (!connectionString) {
    throw new Error("Missing DATABASE_URL environment variable.");
  }
  const client = postgres(connectionString, { prepare: false });
  return drizzle(client, { schema });
}

let _db: ReturnType<typeof createDb> | undefined;

// Lazily created so importing this module never throws at build/prerender
// time when DATABASE_URL isn't set yet — only actually using the db does.
export const db = new Proxy({} as ReturnType<typeof createDb>, {
  get(_, prop, receiver) {
    if (!_db) _db = createDb();
    return Reflect.get(_db, prop, receiver);
  },
});

export { schema };
