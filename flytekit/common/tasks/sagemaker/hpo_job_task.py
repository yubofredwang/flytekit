from __future__ import absolute_import
import datetime as _datetime

from google.protobuf.json_format import MessageToDict

from flytekit import __version__
from flytekit.common.tasks import task as _sdk_task
from flytekit.common import interface as _interface
from flytekit.sdk import types as _sdk_types
from flytekit.models import task as _task_models
from flytekit.models import interface as _interface_model
from flytekit.models.sagemaker import hpo_job as _hpo_job_model
from flytekit.models import literals as _literal_models
from flytekit.common.constants import SdkTaskType
from flyteidl.plugins.sagemaker import hpo_job_pb2 as _hpo_job_pb2
from flytekit.models import literals as _literals, types as _idl_types, \
    task as _task_model
from flytekit.common.tasks.sagemaker.training_job_task import SdkSimpleTrainingJobTask
from flytekit.models.core import types as _core_types


class SdkSimpleHPOJobTask(_sdk_task.SdkTask):

    def __init__(
            self,
            max_number_of_training_jobs: int,
            max_parallel_training_jobs: int,
            training_job: SdkSimpleTrainingJobTask,
            interruptible: bool = False,
            retries: int = 0,
            cacheable: bool = False,
            cache_version: str = "",
    ):
        """

        :param max_number_of_training_jobs:
        :param max_parallel_training_jobs:
        :param training_job:
        :param interruptible:
        :param retries:
        :param cacheable:
        :param cache_version:
        """
        # Use the training job model as a measure of type checking

        hpo_job_custom = _hpo_job_model.HPOJobCustom(
            hpo_job_core=_hpo_job_model.HPOJob(
                max_number_of_training_jobs=max_number_of_training_jobs,
                max_parallel_training_jobs=max_parallel_training_jobs,
                training_job=training_job.training_job_model,
            ),
            training_job_task_template=_task_models.TaskTemplate(
                id=training_job.id,
                type=training_job.type,
                metadata=training_job.metadata,
                interface=training_job.interface,
                custom=training_job.custom,
                container=training_job.container,
            ),
        ).to_flyte_idl()

        # Setting flyte-level timeout to 0, and let SageMaker respect the StoppingCondition of
        #   the underlying training job
        # TODO: Discuss whether this is a viable interface or contract
        timeout = _datetime.timedelta(seconds=0)

        inputs = {
                     "hpo_job_config": _interface_model.Variable(
                         _sdk_types.Types.Proto(_hpo_job_pb2.HPOJobConfig).to_flyte_literal_type(), ""
                     ),
                 }
        inputs.update(training_job.interface.inputs)

        super(SdkSimpleHPOJobTask, self).__init__(
            type=SdkTaskType.SAGEMAKER_HPO_JOB_TASK,
            metadata=_task_models.TaskMetadata(
                runtime=_task_models.RuntimeMetadata(
                    type=_task_models.RuntimeMetadata.RuntimeType.FLYTE_SDK,
                    version=__version__,
                    flavor='sagemaker'
                ),
                discoverable=cacheable,
                timeout=timeout,
                retries=_literal_models.RetryStrategy(retries=retries),
                interruptible=interruptible,
                discovery_version=cache_version,
                deprecated_error_message="",
            ),
            interface=_interface.TypedInterface(
                inputs=inputs,
                outputs={
                    "model": _interface_model.Variable(
                        type=_idl_types.LiteralType(
                            blob=_core_types.BlobType(
                                format="",
                                dimensionality=_core_types.BlobType.BlobDimensionality.SINGLE
                            )
                        ),
                        description=""
                    )
                }
            ),
            custom=MessageToDict(hpo_job_custom),
        )

