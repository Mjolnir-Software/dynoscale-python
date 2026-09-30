declare function dynoscale(options?: dynoscale.DynoscaleOptions): dynoscale.Middleware;

declare namespace dynoscale {
  const VERSION: string;
  function stop(): Promise<void>;

  interface DynoscaleOptions {
    /** BullMQ queues to sample from the web process. */
    bullmq?: {
      queues?: string[];
      connection?: string | Record<string, unknown>;
      prefix?: string;
    };
    /**
     * Return false to keep this process from reporting.
     * The default reports from a non-clustered process and from cluster worker 1.
     */
    isReportingProcess?: () => boolean;
  }

  type Middleware = (
    req: { headers?: Record<string, string | string[] | undefined>; requestBodyWait?: number },
    res: unknown,
    next: (err?: unknown) => void
  ) => Promise<void> | void;
}

export = dynoscale;
