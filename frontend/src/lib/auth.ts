import { betterAuth } from "better-auth";
import { organization } from "better-auth/plugins";
import { Pool } from "pg";

const databaseUrl =
  process.env.DATABASE_URL ?? "postgresql://simba:simba@localhost:5432/simba";

const database = new Pool({
  connectionString: databaseUrl,
});

export const auth = betterAuth({
  database,
  emailAndPassword: {
    enabled: true,
    minPasswordLength: 8,
  },
  session: {
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24, // 1 day
    cookieCache: {
      enabled: true,
      maxAge: 60 * 5, // 5 minutes
    },
  },
  plugins: [
    organization(),
  ],
});

const shouldRunMigrations =
  process.env.NODE_ENV !== "production" &&
  process.env.BETTER_AUTH_AUTO_MIGRATE !== "false";

let migrationsPromise: Promise<void> | null = null;

export const ensureAuthMigrations = async (): Promise<void> => {
  if (!shouldRunMigrations) {
    return;
  }

  if (!migrationsPromise) {
    migrationsPromise = auth.$context.then(async (context) => {
      const contextWithMigrations = context as {
        runMigrations?: () => Promise<void>;
      };

      if (typeof contextWithMigrations.runMigrations === "function") {
        await contextWithMigrations.runMigrations();
      }
    });
  }

  await migrationsPromise;
};

export type Session = typeof auth.$Infer.Session;
