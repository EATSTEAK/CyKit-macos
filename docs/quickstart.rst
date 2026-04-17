Quickstart
==========

Install the package and connect to a supported headset.

.. code-block:: python

   from cykit import CyKitClient, Model

   with CyKitClient(Model.INSIGHT_CONSUMER) as client:
       for sample in client.stream():
           print(sample.eeg)
           break
