"use client";

import {
  CreditCard,
  ArrowUp,
  ArrowUpLeft,
  ArrowFatUp,
} from "@phosphor-icons/react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { loadStripe, Stripe } from "@stripe/stripe-js";
import { usePopup } from "@/components/admin/connectors/Popup";
import { SettingsIcon } from "@/components/icons/icons";
import {
  updateSubscriptionQuantity,
  fetchCustomerPortal,
  statusToDisplay,
  useBillingInformation,
} from "./utils";
import { useEffect } from "react";

export default function BillingInformationPage() {
  const [seats, setSeats] = useState(1);
  const router = useRouter();
  const { popup, setPopup } = usePopup();
  const stripePromise = loadStripe(
    process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!
  );

  const {
    data: billingInformation,
    error,
    isLoading,
    refreshBillingInformation,
  } = useBillingInformation();

  if (error) {
    console.error("Failed to fetch billing information:", error);
  }
  useEffect(() => {
    const url = new URL(window.location.href);
    if (url.searchParams.has("session_id")) {
      setPopup({
        message:
          "Congratulations! Your subscription has been updated successfully.",
        type: "success",
      });
      // Remove the session_id from the URL
      url.searchParams.delete("session_id");
      window.history.replaceState({}, "", url.toString());
      // You might want to refresh the billing information here
      // by calling an API endpoint to get the latest data
    }
  }, [setPopup]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  const handleUpgrade = async () => {
    try {
      const stripe = await stripePromise;

      if (!stripe) throw new Error("Stripe failed to load");
      const response = await updateSubscriptionQuantity(seats);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          `Failed to create checkout session: ${errorData.message || response.statusText}`
        );
      }

      // Leave time for Stripe webhook to get processed
      setTimeout(() => {
        refreshBillingInformation();
      }, 200);
    } catch (error) {
      console.error("Error creating checkout session:", error);
      setPopup({
        message: "Error creating checkout session",
        type: "error",
      });
    }
  };

  const handleManageSubscription = async () => {
    try {
      const response = await fetchCustomerPortal();

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          `Failed to create customer portal session: ${errorData.message || response.statusText}`
        );
      }

      const { url } = await response.json();

      if (!url) {
        throw new Error("No portal URL returned from the server");
      }

      // Redirect to the Stripe Customer Portal
      router.push(url);
    } catch (error) {
      console.error("Error creating customer portal session:", error);
      setPopup({
        message: "Error creating customer portal session",
        type: "error",
      });
    }
  };
  if (!billingInformation) {
    return <div>Loading...</div>;
  }

  return (
    <div className="space-y-8">
      <div className="bg-gray-50 rounded-lg p-8 border border-gray-200">
        {popup}

        <h2 className="text-2xl font-bold mb-6 text-gray-800 flex items-center">
          <CreditCard className="mr-4 text-gray-600" size={24} />
          Billing Information
        </h2>

        <div className="space-y-4">
          <div className="bg-white p-5 rounded-lg shadow-sm transition-all duration-300 hover:shadow-md">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-lg font-medium text-gray-700">Seats</p>
                <p className="text-sm text-gray-500">
                  Number of licensed users
                </p>
              </div>
              <p className="text-xl font-semibold text-gray-900">
                {billingInformation.seats}
              </p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-lg shadow-sm transition-all duration-300 hover:shadow-md">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-lg font-medium text-gray-700">
                  Subscription Status
                </p>
                <p className="text-sm text-gray-500">
                  Current state of your subscription
                </p>
              </div>
              <p className="text-xl font-semibold text-gray-900">
                {statusToDisplay(billingInformation.subscriptionStatus)}
              </p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-lg shadow-sm transition-all duration-300 hover:shadow-md">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-lg font-medium text-gray-700">
                  Billing Start
                </p>
                <p className="text-sm text-gray-500">
                  Start date of current billing cycle
                </p>
              </div>
              <p className="text-xl font-semibold text-gray-900">
                {new Date(billingInformation.billingStart).toLocaleDateString()}
              </p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-lg shadow-sm transition-all duration-300 hover:shadow-md">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-lg font-medium text-gray-700">Billing End</p>
                <p className="text-sm text-gray-500">
                  End date of current billing cycle
                </p>
              </div>
              <p className="text-xl font-semibold text-gray-900">
                {new Date(billingInformation.billingEnd).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>

        {!billingInformation.paymentMethodEnabled && (
          <div className="mt-4 p-4 bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700">
            <p className="font-bold">Notice:</p>
            <p>
              You'll need to add a payment method before your trial ends to
              continue using the service.
            </p>
          </div>
        )}
        {billingInformation.subscriptionStatus === "trialing" ? (
          <div className="bg-white p-5 rounded-lg shadow-sm transition-all duration-300 hover:shadow-md mt-8">
            <p className="text-lg font-medium text-gray-700">
              No cap on users during trial
            </p>
          </div>
        ) : (
          <div className="flex items-center space-x-4 mt-8">
            <input
              type="number"
              min="1"
              value={seats}
              onChange={(e) => setSeats(Number(e.target.value))}
              className="border border-gray-300 rounded-md px-4 py-2 w-32 focus:outline-none focus:ring-2 focus:ring-gray-500 bg-white text-gray-800 shadow-sm transition-all duration-300"
              placeholder="Seats"
            />

            <button
              onClick={handleUpgrade}
              className="bg-gray-600 text-white px-6 py-2 rounded-md hover:bg-gray-700 transition duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-opacity-50 font-medium shadow-md text-lg"
            >
              Upgrade Seats
            </button>
          </div>
        )}
      </div>

      <div className="bg-white p-5 rounded-lg shadow-sm transition-all duration-300 hover:shadow-md">
        <div className="flex justify-between items-center mb-4">
          <div>
            <p className="text-lg font-medium text-gray-700">
              Manage Subscription
            </p>
            <p className="text-sm text-gray-500">
              View your plan, update payment, or change subscription
            </p>
          </div>
          <SettingsIcon className="text-gray-600" size={20} />
        </div>
        <button
          onClick={handleManageSubscription}
          className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-opacity-50 font-medium shadow-sm text-sm flex items-center justify-center"
        >
          <ArrowFatUp className="mr-2" size={16} />
          Manage Subscription
        </button>
      </div>
    </div>
  );
}
