"use client";

import { DeleteChemicalButton, DeleteCustomerButton } from "@/components/demand/DemandDeleteButtons";
import Link from "next/link";
import { useMemo, useState } from "react";

type CustomerItem = {
  id: string;
  account_name: string;
};

type ChemicalItem = {
  id: string;
  name: string;
};

type DemandSearchListsProps = {
  customers: CustomerItem[];
  chemicals: ChemicalItem[];
};

function matchesQuery(value: string, query: string): boolean {
  if (!query) return true;
  return value.toLowerCase().includes(query.toLowerCase());
}

export function DemandSearchLists({ customers, chemicals }: DemandSearchListsProps) {
  const [customerQuery, setCustomerQuery] = useState("");
  const [chemicalQuery, setChemicalQuery] = useState("");

  const filteredCustomers = useMemo(
    () => customers.filter((c) => matchesQuery(c.account_name, customerQuery)),
    [customers, customerQuery],
  );
  const filteredChemicals = useMemo(
    () => chemicals.filter((ch) => matchesQuery(ch.name, chemicalQuery)),
    [chemicals, chemicalQuery],
  );

  return (
    <>
      <section className="mt-10 rounded-lg border border-neutral-700 bg-neutral-900/70 p-6">
        <h2 className="text-lg font-medium text-neutral-200">Customers</h2>
        <p className="mt-2 text-sm text-neutral-300">
          Open a customer to edit service day, frequency, tech, and chemical quantities.
        </p>
        <div className="mt-4">
          <label htmlFor="customer_search" className="text-xs text-neutral-200">
            Search customers
          </label>
          <input
            id="customer_search"
            value={customerQuery}
            onChange={(e) => setCustomerQuery(e.target.value)}
            placeholder="Type account name..."
            className="mt-1 w-full rounded border border-neutral-500 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus-visible:ring-2 focus-visible:ring-sky-400 focus-visible:ring-offset-2 focus-visible:ring-offset-neutral-900"
          />
        </div>
        {customers.length === 0 ? (
          <p className="mt-4 text-sm text-neutral-300">No customers yet.</p>
        ) : filteredCustomers.length === 0 ? (
          <p className="mt-4 text-sm text-neutral-300">No customers match your search.</p>
        ) : (
          <ul className="mt-4 divide-y divide-neutral-700 rounded border border-neutral-700">
            {filteredCustomers.map((c) => (
              <li
                key={c.id}
                className="flex items-center justify-between gap-3 px-4 py-3 hover:bg-neutral-800/70"
              >
                <Link
                  href={`/dashboard/demand/customers/${c.id}`}
                  className="min-w-0 flex-1 rounded-sm text-sm text-sky-300 hover:text-sky-200 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400"
                >
                  {c.account_name}
                </Link>
                <DeleteCustomerButton customerId={c.id} accountName={c.account_name} />
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="mt-10 rounded-lg border border-neutral-700 bg-neutral-900/70 p-6">
        <h2 className="text-lg font-medium text-neutral-200">Chemical catalog</h2>
        <p className="mt-2 text-sm text-neutral-300">
          Deleting a chemical removes it from the catalog and clears its quantities for every
          customer.
        </p>
        <div className="mt-4">
          <label htmlFor="chemical_search" className="text-xs text-neutral-200">
            Search chemicals
          </label>
          <input
            id="chemical_search"
            value={chemicalQuery}
            onChange={(e) => setChemicalQuery(e.target.value)}
            placeholder="Type chemical name..."
            className="mt-1 w-full rounded border border-neutral-500 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus-visible:ring-2 focus-visible:ring-sky-400 focus-visible:ring-offset-2 focus-visible:ring-offset-neutral-900"
          />
        </div>
        {chemicals.length === 0 ? (
          <p className="mt-4 text-sm text-neutral-300">No chemicals yet.</p>
        ) : filteredChemicals.length === 0 ? (
          <p className="mt-4 text-sm text-neutral-300">No chemicals match your search.</p>
        ) : (
          <ul className="mt-4 divide-y divide-neutral-700 rounded border border-neutral-700">
            {filteredChemicals.map((ch) => (
              <li
                key={ch.id}
                className="flex items-center justify-between gap-3 px-4 py-3 hover:bg-neutral-800/70"
              >
                <span className="min-w-0 flex-1 text-sm text-neutral-200">{ch.name}</span>
                <DeleteChemicalButton chemicalId={ch.id} chemicalName={ch.name} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}
