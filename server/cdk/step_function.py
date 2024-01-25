#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

from aws_cdk import (
    aws_stepfunctions as _aws_stepfunctions,
    aws_stepfunctions_tasks as _aws_stepfunctions_tasks,
    Duration,
    aws_logs as logs,
)
from aws_cdk.aws_stepfunctions import JsonPath


class StepFunctionStack:
    def __init__(self, cdk_scope):

        # Environment Variables that need to be set to the processing container jobs
        container_overrides = _aws_stepfunctions_tasks.BatchContainerOverrides(
            environment={
                "BUCKET": _aws_stepfunctions.JsonPath.string_at("$.event.bucket"),
                "KEY": _aws_stepfunctions.JsonPath.string_at("$.event.key"),
                "output_s3_key": _aws_stepfunctions.JsonPath.string_at(
                    "$.event.output_s3_key"
                ),
                "audio_wav_file": _aws_stepfunctions.JsonPath.string_at("$.event.audio_wav_file"),
                "diarization_file": _aws_stepfunctions.JsonPath.string_at(
                    "$.event.diarization_file"
                ),
                "audio_chunks_s3_key": _aws_stepfunctions.JsonPath.string_at(
                    "$.event.audio_chunks_s3_key"
                ),
                "content_type": _aws_stepfunctions.JsonPath.string_at(
                    "$.event.content_type"
                ),
                "output_file": _aws_stepfunctions.JsonPath.string_at(
                    "$.event.output_file"
                ),
                "groups": _aws_stepfunctions.JsonPath.string_at("$.event.groups"),
                "txt_chunks_s3_key": _aws_stepfunctions.JsonPath.string_at(
                    "$.event.txt_chunks_s3_key"
                ),
                "original_transcription_file": _aws_stepfunctions.JsonPath.string_at(
                    "$.event.original_transcription_file"
                ),
                "input_file": _aws_stepfunctions.JsonPath.string_at(
                    "$.event.input_file"
                ),
                "dominant_language_code": _aws_stepfunctions.JsonPath.string_at(
                    "$.event.dominant_language_code"
                ),
                "dominant_language": _aws_stepfunctions.JsonPath.string_at(
                    "$.event.dominant_language"
                ),
            }
        )

        # All Step Definitions corresponding to Lambda Functions & Batch Jobs
        check_file_type_step = _aws_stepfunctions_tasks.LambdaInvoke(
            cdk_scope,
            id="CheckFileType",
            lambda_function=cdk_scope.check_input_file_type_fn,
            output_path="$.Payload",
        )

        convert_to_wav_step = _aws_stepfunctions_tasks.BatchSubmitJob(
            cdk_scope,
            "ConvertToWAV",
            job_definition_arn=cdk_scope.mp3_to_wav_job_def.job_definition_arn,
            job_name="convert_to_wav_job",
            job_queue_arn=cdk_scope.mp3_to_wav_job_queue.job_queue_arn,
            container_overrides=container_overrides,
            result_path=JsonPath.DISCARD,
        )

        diarization_fn_step = _aws_stepfunctions_tasks.LambdaInvoke(
            cdk_scope,
            id="Diarization",
            lambda_function=cdk_scope.diarization_fn,
            output_path="$.Payload",
        )

        check_diarization_output_fn_step = _aws_stepfunctions_tasks.LambdaInvoke(
            cdk_scope,
            id="CheckDiarizationOutput",
            lambda_function=cdk_scope.check_diarization_output_fn,
            output_path="$.Payload",
        )

        transcription_fn_step = _aws_stepfunctions_tasks.LambdaInvoke(
            cdk_scope,
            id="Transcription",
            lambda_function=cdk_scope.transcription_fn,
            output_path="$.Payload",
        )

        translation_fn_step = _aws_stepfunctions_tasks.LambdaInvoke(
            cdk_scope,
            id="Translation",
            lambda_function=cdk_scope.transcription_fn,
            output_path="$.Payload",
        )

        transcription_output_fn_step = _aws_stepfunctions_tasks.LambdaInvoke(
            cdk_scope,
            id="TranscriptionOutputCheck",
            lambda_function=cdk_scope.transcription_output_fn,
            output_path="$.Payload",
        )

        translation_output_fn_step = _aws_stepfunctions_tasks.LambdaInvoke(
            cdk_scope,
            id="TranslationOutputCheck",
            lambda_function=cdk_scope.transcription_output_fn,
            output_path="$.Payload",
        )

        combine_file_output_fn_step = _aws_stepfunctions_tasks.LambdaInvoke(
            cdk_scope,
            id="CombineTranscriptionOutput",
            lambda_function=cdk_scope.combine_file_output_fn,
            output_path="$.Payload",
        )

        combine_translation_file_output_fn_step = _aws_stepfunctions_tasks.LambdaInvoke(
            cdk_scope,
            id="CombineTranslationOutput",
            lambda_function=cdk_scope.combine_file_output_fn,
            output_path="$.Payload",
        )

        chunking_step = _aws_stepfunctions_tasks.BatchSubmitJob(
            cdk_scope,
            "Chunking",
            job_definition_arn=cdk_scope.chunking_job_def.job_definition_arn,
            job_name="chunking_job",
            job_queue_arn=cdk_scope.chunking_job_queue.job_queue_arn,
            container_overrides=container_overrides,
            result_path=JsonPath.DISCARD,
        )

        detect_language_step = _aws_stepfunctions_tasks.LambdaInvoke(
            cdk_scope,
            id="DetectLanguage",
            lambda_function=cdk_scope.detect_language_fn,
            output_path="$.Payload",
        )

        start_comprehension_step = _aws_stepfunctions_tasks.LambdaInvoke(
            cdk_scope,
            id="StartComprehendJobs",
            lambda_function=cdk_scope.start_comprehension_fn,
            output_path="$.Payload",
        )

        check_sentiment_job_step = _aws_stepfunctions_tasks.LambdaInvoke(
            cdk_scope,
            id="CheckSentimentJob",
            lambda_function=cdk_scope.check_sentiment_job_fn,
            output_path="$.Payload",
        )

        check_entities_job_step = _aws_stepfunctions_tasks.LambdaInvoke(
            cdk_scope,
            id="CheckEntitiesJob",
            lambda_function=cdk_scope.check_entities_job_fn,
            output_path="$.Payload",
        )

        summarize_step = _aws_stepfunctions_tasks.LambdaInvoke(
            cdk_scope,
            id="Summarize",
            lambda_function=cdk_scope.summarize_fn,
            output_path="$.Payload",
        )

        post_processing_step = _aws_stepfunctions_tasks.LambdaInvoke(
            cdk_scope,
            id="PostProcessing",
            lambda_function=cdk_scope.post_processing_fn,
            output_path="$.Payload",
        )

        # Operational Steps for waiting, success and failure
        wait_for_sentiment_job = _aws_stepfunctions.Wait(
            cdk_scope,
            "WaitForSentimentJob",
            time=_aws_stepfunctions.WaitTime.duration(Duration.seconds(60)),
        )

        wait_for_entities_job = _aws_stepfunctions.Wait(
            cdk_scope,
            "WaitForEntitiesJob",
            time=_aws_stepfunctions.WaitTime.duration(Duration.seconds(30)),
        )

        wait_for_diarization_job = _aws_stepfunctions.Wait(
            cdk_scope,
            "WaitForDiarizationJob",
            time=_aws_stepfunctions.WaitTime.duration(Duration.seconds(30)),
        )

        fail_job = _aws_stepfunctions.Fail(
            cdk_scope,
            id="FailureStep",
            cause="Conversation Intelligence failed",
            error="Conversation Intelligence failed",
        )

        succeed_job = _aws_stepfunctions.Succeed(
            cdk_scope, id="SuccessStep", comment="Conversation Analysis Succeeded"
        )

        if_lang_code_is_english = _aws_stepfunctions.Condition.string_equals(
            "$.event.dominant_language_code", "en"
        )

        if_file_type_is_mp3 = _aws_stepfunctions.Condition.string_matches(
            "$.content_type", "*mp3"
        )

        should_retry_transcription_check = _aws_stepfunctions.Condition.boolean_equals(
            "$.event.transcription_complete", False
        )

        should_retry_diarization_check = _aws_stepfunctions.Condition.boolean_equals(
            "$.event.diarization_complete", False
        )

        if_file_type_is_text = _aws_stepfunctions.Condition.string_equals(
            "$.content_type", "text/plain"
        )

        if_file_type_is_wav = _aws_stepfunctions.Condition.string_matches(
            "$.content_type", "*wav"
        )

        wait_for_transcription_job = _aws_stepfunctions.Wait(
            cdk_scope,
            "WaitForTranscriptionJob",
            time=_aws_stepfunctions.WaitTime.duration(Duration.seconds(120)),
        )

        wait_for_translation_job = _aws_stepfunctions.Wait(
            cdk_scope,
            "WaitForTranslationJob",
            time=_aws_stepfunctions.WaitTime.duration(Duration.seconds(120)),
        )

        # Step Function Chain Defintions
        post_transcription_chain = start_comprehension_step.add_retry(
            backoff_rate=2,
            max_attempts=10,
            errors=[
                "TooManyRequestsException"
            ],
            interval=Duration.minutes(10),
        ).next(
            _aws_stepfunctions.Parallel(cdk_scope, "CheckComprehendJobStatus")
            .branch(
                wait_for_sentiment_job.next(
                    # Detect Sentiment Job Status after waiting for 5 seconds
                    check_sentiment_job_step.next(
                        _aws_stepfunctions.Choice(cdk_scope, "CheckSentimentJobStatus?")
                        .when(
                            _aws_stepfunctions.Condition.boolean_equals(
                                "$.event.sentiment_job_status", True
                            ),
                            _aws_stepfunctions.Succeed(cdk_scope, "SentimentJobCompleted"),
                        )
                        .otherwise(wait_for_sentiment_job)
                    )
                )
            )
            .branch(
                wait_for_entities_job.next(
                    check_entities_job_step.next(
                        _aws_stepfunctions.Choice(
                            cdk_scope,
                            "CheckEntitiesJobStatus?",
                        )
                        .when(
                            _aws_stepfunctions.Condition.boolean_equals(
                                "$.event.entities_job_status",
                                True,
                            ),
                            _aws_stepfunctions.Succeed(cdk_scope, "EntitiesJobCompleted"),
                        )
                        .otherwise(wait_for_entities_job)
                    )
                )
            )
            .next(summarize_step.next(post_processing_step.next(succeed_job)))
        )

        translation_chain = combine_file_output_fn_step.next(
            # Detect Language Step
            detect_language_step.next(
                _aws_stepfunctions.Choice(
                    cdk_scope,
                    "ShouldTranslate?",
                )
                .when(
                    (if_file_type_is_mp3.not_(if_lang_code_is_english)).or_(
                        if_file_type_is_wav.not_(if_lang_code_is_english)
                    ),
                    translation_fn_step.next(
                        wait_for_translation_job.next(
                            translation_output_fn_step.next(
                                _aws_stepfunctions.Choice(
                                    cdk_scope,
                                    "WereChunksTranslated?",
                                )
                                .when(
                                    should_retry_transcription_check,
                                    wait_for_translation_job,
                                )
                                .otherwise(
                                    combine_translation_file_output_fn_step.next(
                                        post_transcription_chain
                                    )
                                )
                            )
                        )
                    )
                )
                .otherwise(
                    post_transcription_chain
                )
            )
        )

        transcription_chain = transcription_fn_step.next(
            wait_for_transcription_job.next(
                transcription_output_fn_step.next(
                    _aws_stepfunctions.Choice(
                        cdk_scope,
                        "WereChunksTranscribed?",
                    )
                    .when(should_retry_transcription_check, wait_for_transcription_job)
                    .otherwise(
                        translation_chain
                    )
                )
            )
        )

        pre_transcription_chain = check_file_type_step.next(
            _aws_stepfunctions.Choice(cdk_scope, "FileType?")
            .when(
                if_file_type_is_mp3,
                convert_to_wav_step.next(diarization_fn_step),
            )
            .when(
                if_file_type_is_text,
                post_transcription_chain,
            )
            .when(
                if_file_type_is_wav,
                diarization_fn_step.add_catch(fail_job).next(
                    # Add State to Wait 30 Seconds before checking next
                    wait_for_diarization_job.next(
                        _aws_stepfunctions.Choice(cdk_scope, "DiarizationFileDownloaded?")
                        .when(
                            should_retry_diarization_check,
                            check_diarization_output_fn_step.next(
                                wait_for_diarization_job
                            ),
                        )
                        .otherwise(
                            chunking_step.add_catch(fail_job).next(transcription_chain)
                        )
                    )
                ),
            )
            .otherwise(fail_job)
        )

        step_fn_log_group = logs.LogGroup(
            cdk_scope, "ci_stepfn_logs"
        )

        ci_step = _aws_stepfunctions.StateMachine(
            cdk_scope,
            id="ci_workflow",
            definition=pre_transcription_chain,
            state_machine_type=_aws_stepfunctions.StateMachineType.STANDARD,
            logs=_aws_stepfunctions.LogOptions(
                destination=step_fn_log_group,
                include_execution_data=True,
                level=_aws_stepfunctions.LogLevel.ALL,
            ),
        )

        self.ci_step = ci_step
