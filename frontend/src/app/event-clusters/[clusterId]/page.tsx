import { getActiveCompany, getEventClusterDetail } from "@/lib/api";

export default async function EventClusterDetailPage({
  params,
}: {
  params: Promise<{ clusterId: string }>;
}) {
  const { clusterId } = await params;
  const company = await getActiveCompany();
  const cluster = await getEventClusterDetail(company.id, Number(clusterId));

  return (
    <main className="px-6 py-8">
      <div className="mx-auto max-w-6xl">
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">Event Detail</p>
        <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">{cluster.title ?? "Untitled event"}</h2>
        <p className="mt-3 text-sm text-slate-400">{cluster.members.length} member articles for {company.name}</p>
        <div className="mt-8 space-y-4">
          {cluster.members.length === 0 ? <p className="text-slate-400">No member articles are available.</p> : cluster.members.map((member) => (
            <article key={member.article_id} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
              <a href={member.url} target="_blank" rel="noreferrer" className="text-lg font-semibold text-white hover:text-cyan-300">{member.title}</a>
              <p className="mt-2 text-sm text-slate-400">{member.source_name} · {member.published_at ?? "Date unavailable"}</p>
            </article>
          ))}
        </div>
      </div>
    </main>
  );
}
